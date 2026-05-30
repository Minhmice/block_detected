"""CLS-01/02: warp face classification (TFLite when available, stub for dev/tests)."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Optional, Protocol, runtime_checkable

import numpy as np

from .detection_contract import BLOCK_ID_TO_LABEL, BlockID, BlockLabel


@dataclass(frozen=True)
class ClassifierSettings:
    model_path: Optional[str] = None
    min_confidence: float = 0.55
    backend: str = "stub"

    def __post_init__(self) -> None:
        if not 0.0 <= self.min_confidence <= 1.0:
            raise ValueError("min_confidence must be in [0, 1]")
        if self.backend not in ("stub", "tflite"):
            raise ValueError("backend must be 'stub' or 'tflite'")


@dataclass(frozen=True)
class ClassificationResult:
    block_id: BlockID
    label: BlockLabel
    confidence: float
    raw_score: float


@runtime_checkable
class FaceClassifier(Protocol):
    def classify(self, warped_bgr: np.ndarray) -> ClassificationResult: ...


class StubFaceClassifier:
    """Deterministic dev classifier from mean BGR (tests and offline dev)."""

    def classify(self, warped_bgr: np.ndarray) -> ClassificationResult:
        if warped_bgr.ndim != 3 or warped_bgr.shape[2] != 3:
            raise ValueError("warped_bgr must be H×W×3 BGR")
        mean_b, mean_g, mean_r = [float(x) for x in warped_bgr.mean(axis=(0, 1))]
        # Map channel dominance to block id 1–4 for repeatable tests.
        if mean_r >= mean_g and mean_r >= mean_b:
            block_id = BlockID.BLOCK_01
            confidence = 0.92
        elif mean_g >= mean_b:
            block_id = BlockID.BLOCK_02
            confidence = 0.88
        elif mean_b >= mean_r:
            block_id = BlockID.BLOCK_03
            confidence = 0.85
        else:
            block_id = BlockID.BLOCK_04
            confidence = 0.80
        return ClassificationResult(
            block_id=block_id,
            label=BLOCK_ID_TO_LABEL[block_id],
            confidence=confidence,
            raw_score=confidence,
        )


class TfliteFaceClassifier:
    """INT8 TFLite classifier (optional dependency)."""

    def __init__(self, model_path: str) -> None:
        path = Path(model_path)
        if not path.is_file():
            raise FileNotFoundError(f"TFLite model not found: {model_path}")
        try:
            import tflite_runtime.interpreter as tflite  # type: ignore[import-untyped]
        except ImportError:
            from tensorflow.lite import Interpreter as tflite_interpreter  # type: ignore

            class _Interp:
                def __init__(self, p: str) -> None:
                    self._inner = tflite_interpreter(model_path=p)

                def allocate_tensors(self) -> None:
                    self._inner.allocate_tensors()

                def get_input_details(self) -> list:
                    return self._inner.get_input_details()

                def get_output_details(self) -> list:
                    return self._inner.get_output_details()

                def set_tensor(self, i: int, v: object) -> None:
                    self._inner.set_tensor(i, v)

                def invoke(self) -> None:
                    self._inner.invoke()

                def get_tensor(self, i: int) -> object:
                    return self._inner.get_tensor(i)

            tflite = type("tflite", (), {"Interpreter": _Interp})  # type: ignore

        self._interpreter = tflite.Interpreter(model_path=str(path))
        self._interpreter.allocate_tensors()
        self._input = self._interpreter.get_input_details()[0]
        self._output = self._interpreter.get_output_details()[0]

    def classify(self, warped_bgr: np.ndarray) -> ClassificationResult:
        import cv2

        h, w = self._input["shape"][1:3]
        rgb = cv2.cvtColor(warped_bgr, cv2.COLOR_BGR2RGB)
        resized = cv2.resize(rgb, (w, h), interpolation=cv2.INTER_AREA)
        inp = resized.astype(np.float32) / 255.0
        if len(self._input["shape"]) == 4:
            inp = np.expand_dims(inp, axis=0)
        self._interpreter.set_tensor(self._input["index"], inp)
        self._interpreter.invoke()
        logits = np.asarray(self._interpreter.get_tensor(self._output["index"])).reshape(-1)
        idx = int(np.argmax(logits))
        score = float(logits[idx])
        if idx < 0 or idx >= 4:
            raise RuntimeError(f"unexpected class index {idx}")
        block_id = BlockID(idx + 1)
        exp = np.exp(logits - logits.max())
        probs = exp / exp.sum()
        confidence = float(probs[idx])
        return ClassificationResult(
            block_id=block_id,
            label=BLOCK_ID_TO_LABEL[block_id],
            confidence=confidence,
            raw_score=score,
        )


def create_classifier(settings: ClassifierSettings) -> FaceClassifier:
    if settings.backend == "tflite":
        if not settings.model_path:
            raise ValueError("model_path required for tflite backend")
        return TfliteFaceClassifier(settings.model_path)
    return StubFaceClassifier()


def classify_face(
    warped_bgr: np.ndarray,
    settings: ClassifierSettings | None = None,
    classifier: FaceClassifier | None = None,
) -> ClassificationResult:
    settings = settings or ClassifierSettings()
    clf = classifier or create_classifier(settings)
    return clf.classify(warped_bgr)

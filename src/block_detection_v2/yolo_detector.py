"""YOLO block detection first-pass for block_detection_v2.

Uses Ultralytics only. Model: models/rbs-final.pt at repo root.
Classical CV (roi/fit/score) runs on YOLO crops in Phase 18 wiring.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import List, Optional, Sequence

import numpy as np

from . import config

_REPO_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_MODEL_PATH = Path(config.YOLO_MODEL_PATH)

DEFAULT_CONF = config.YOLO_CONF
DEFAULT_IOU = config.YOLO_IOU
DEFAULT_MAX_DET = 32


@dataclass(frozen=True)
class YoloBlockBox:
    """Axis-aligned detection from YOLO."""

    x1: int
    y1: int
    x2: int
    y2: int
    confidence: float
    class_id: int
    class_name: str

    @property
    def width(self) -> int:
        return max(0, self.x2 - self.x1)

    @property
    def height(self) -> int:
        return max(0, self.y2 - self.y1)

    @property
    def area(self) -> int:
        return self.width * self.height

    @property
    def center(self) -> tuple[float, float]:
        return ((self.x1 + self.x2) / 2.0, (self.y1 + self.y2) / 2.0)

    def as_xyxy(self) -> tuple[int, int, int, int]:
        return (self.x1, self.y1, self.x2, self.y2)

    def as_dict(self) -> dict:
        return {
            "xyxy": list(self.as_xyxy()),
            "confidence": self.confidence,
            "class_id": self.class_id,
            "class_name": self.class_name,
            "center": list(self.center),
            "area": self.area,
        }


class YoloBlockDetector:
    """Thin Ultralytics wrapper — detect LEGO blocks before classical CV."""

    def __init__(
        self,
        model_path: Path | str | None = None,
        *,
        conf: float = DEFAULT_CONF,
        iou: float = DEFAULT_IOU,
        max_det: int = DEFAULT_MAX_DET,
        device: str | int | None = None,
    ) -> None:
        self._model_path = Path(model_path) if model_path else DEFAULT_MODEL_PATH
        self.conf = conf
        self.iou = iou
        self.max_det = max_det
        self.device = config.YOLO_DEVICE if device is None else device
        self._model = None

    @property
    def model_path(self) -> Path:
        return self._model_path

    def _ensure_model(self):
        if self._model is not None:
            return self._model
        if not self._model_path.is_file():
            raise FileNotFoundError(f"YOLO model not found: {self._model_path}")
        from ultralytics import YOLO

        self._model = YOLO(str(self._model_path))
        return self._model

    def detect(self, frame: np.ndarray) -> List[YoloBlockBox]:
        """Run YOLO on a BGR frame; return boxes sorted by confidence desc."""
        if frame is None or frame.size == 0:
            return []

        model = self._ensure_model()
        results = model.predict(
            source=frame,
            conf=self.conf,
            iou=self.iou,
            max_det=self.max_det,
            device=self.device,
            verbose=False,
        )

        boxes: List[YoloBlockBox] = []
        for result in results:
            names = result.names or {}
            if result.boxes is None:
                continue
            for row in result.boxes:
                xyxy = row.xyxy[0].tolist()
                x1, y1, x2, y2 = (int(v) for v in xyxy)
                cls_id = int(row.cls[0].item()) if row.cls is not None else -1
                conf = float(row.conf[0].item()) if row.conf is not None else 0.0
                cls_name = str(names.get(cls_id, str(cls_id)))
                boxes.append(
                    YoloBlockBox(
                        x1=x1,
                        y1=y1,
                        x2=x2,
                        y2=y2,
                        confidence=conf,
                        class_id=cls_id,
                        class_name=cls_name,
                    )
                )

        boxes.sort(key=lambda b: b.confidence, reverse=True)
        return boxes

    def detect_dicts(self, frame: np.ndarray) -> List[dict]:
        return [b.as_dict() for b in self.detect(frame)]

    def best(self, frame: np.ndarray) -> Optional[YoloBlockBox]:
        found = self.detect(frame)
        return found[0] if found else None

    def crop(self, frame: np.ndarray, box: YoloBlockBox, pad_frac: float = 0.05) -> np.ndarray:
        """Crop frame to box with optional fractional padding."""
        h, w = frame.shape[:2]
        pad_x = int(box.width * pad_frac)
        pad_y = int(box.height * pad_frac)
        x1 = max(0, box.x1 - pad_x)
        y1 = max(0, box.y1 - pad_y)
        x2 = min(w, box.x2 + pad_x)
        y2 = min(h, box.y2 + pad_y)
        return frame[y1:y2, x1:x2].copy()

    def crops(
        self,
        frame: np.ndarray,
        boxes: Optional[Sequence[YoloBlockBox]] = None,
        *,
        pad_frac: float = 0.05,
    ) -> List[np.ndarray]:
        boxes = list(boxes) if boxes is not None else self.detect(frame)
        return [self.crop(frame, b, pad_frac=pad_frac) for b in boxes]

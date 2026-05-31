"""Reference image tests — all four standard block types detected."""

from __future__ import annotations

import json
import sys
from pathlib import Path
from unittest import mock

import cv2
import numpy as np
import pytest

from app.services.edge_impulse_runner import EdgeImpulseRunnerService
from app.services.eim_model import get_model_by_id, resolve_eim_path
from app.services.eim_runtime import eim_runtime
from block_detected.pipeline import PipelineSettings

FIXTURE_PATH = (
    Path(__file__).resolve().parent
    / "fixtures"
    / "vision"
    / "four_pallets_reference.png"
)


def load_reference_frame() -> np.ndarray:
    bgr = cv2.imread(str(FIXTURE_PATH))
    assert bgr is not None, f"missing fixture: {FIXTURE_PATH}"
    if bgr.shape[:2] != (480, 640):
        bgr = cv2.resize(bgr, (640, 480))
    return bgr


def _load_vision_settings() -> PipelineSettings:
    repo_root = Path(__file__).resolve().parents[1]
    config_path = repo_root / "config" / "vision.example.json"
    data = json.loads(config_path.read_text(encoding="utf-8"))
    from block_detected.detector import DetectorSettings
    from block_detected.preprocess import PreprocessSettings
    from block_detected.vision import VisionSettings

    preprocess = data.get("preprocess", {})
    detector = data.get("detector", {})
    blur = preprocess.get("blur_kernel", [5, 5])
    return PipelineSettings(
        vision=VisionSettings(
            preprocess=PreprocessSettings(
                blur_kernel=(int(blur[0]), int(blur[1])),
                adaptive_block_size=int(preprocess.get("adaptive_block_size", 31)),
                adaptive_c=int(preprocess.get("adaptive_c", 5)),
                canny_low=int(preprocess.get("canny_low", 50)),
                canny_high=int(preprocess.get("canny_high", 150)),
            ),
            detector=DetectorSettings(
                min_area_px=float(detector.get("min_area_px", 400)),
                max_area_px=float(detector.get("max_area_px", 80000)),
                aspect_min=float(detector.get("aspect_min", 0.75)),
                aspect_max=float(detector.get("aspect_max", 1.33)),
            ),
        ),
        min_face_area_px=float(detector.get("min_area_px", 400)) * 0.25,
    )


def _mock_ei_modules(fake_runner: mock.Mock) -> dict[str, mock.Mock]:
    image_mod = mock.MagicMock()
    image_mod.ImageImpulseRunner = mock.Mock(return_value=fake_runner)
    pkg = mock.MagicMock()
    return {
        "edge_impulse_linux": pkg,
        "edge_impulse_linux.image": image_mod,
    }


def test_reference_four_block_types_with_mocked_ei(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    model = tmp_path / "model.eim"
    model.write_text("fake", encoding="utf-8")
    model.chmod(0o755)
    monkeypatch.setenv("EI_MODEL_PATH", str(model))

    labels = ["block_01", "block_02", "block_03", "block_04"]

    def classify_side_effect(_features):
        if not hasattr(classify_side_effect, "calls"):
            classify_side_effect.calls = 0
        label = labels[classify_side_effect.calls % 4]
        classify_side_effect.calls += 1
        return {"result": {"classification": {label: 0.95, "block_01": 0.01}}}

    fake_runner = mock.Mock()
    fake_runner.init = mock.Mock(return_value={})
    fake_runner.get_features_from_image = mock.Mock(
        return_value=(np.zeros(10, dtype=np.float32), None)
    )
    fake_runner.classify = mock.Mock(side_effect=classify_side_effect)

    service = EdgeImpulseRunnerService(min_confidence=0.5)
    settings = _load_vision_settings()
    frame = load_reference_frame()

    with mock.patch.dict(sys.modules, _mock_ei_modules(fake_runner)):
        detected = service.detect_block_types_in_frame(frame, settings)

    assert detected == {1, 2, 3, 4}


@pytest.mark.parametrize("model_id", ["minhmice-v2", "shit-v1"])
def test_reference_four_block_types_live_eim(
    model_id: str,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    entry = get_model_by_id(model_id)
    if entry is None or not entry.executable:
        pytest.skip(f"model not available: {model_id}")
    if not __import__("platform").machine() == "aarch64":
        pytest.skip("live EIM requires aarch64 Pi hardware")

    monkeypatch.setenv("VISION_MOCK_MODE", "false")
    monkeypatch.delenv("EI_MODEL_PATH", raising=False)
    eim_runtime.reset_for_tests()
    eim_runtime.set_selected_id(model_id)

    service = EdgeImpulseRunnerService(min_confidence=0.4)
    service.reload()
    settings = _load_vision_settings()
    frame = load_reference_frame()

    detected = service.detect_block_types_in_frame(frame, settings)
    missing = {1, 2, 3, 4} - detected
    assert not missing, f"model {model_id} missing block types: {missing}; got {detected}"

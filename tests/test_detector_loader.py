"""Tests for DetectorBackend protocol compliance and loader indirection."""

from pathlib import Path

from block_detected.core.domain import FrameResult
from block_detected.core.protocols import DetectorBackend
from block_detected.runtime.detector_loader import load_detector


class _FakeDetector:
    def __init__(self, name: str = "m.pt") -> None:
        self._name = name

    @property
    def model_name(self) -> str:
        return self._name

    def predict(self, frame, *, conf: float):
        return FrameResult(detections=[], raw=None)

    def close(self) -> None:
        pass


def test_fake_detector_satisfies_detector_backend_protocol():
    detector = _FakeDetector("test.pt")
    assert isinstance(detector, DetectorBackend)


def test_load_detector_returns_monkeypatched_fake(monkeypatch):
    fake = _FakeDetector("patched.pt")

    monkeypatch.setattr(
        "block_detected.runtime.detector_loader.YoloDetector",
        lambda _path: fake,
    )

    loaded = load_detector(Path("any.pt"))

    assert loaded is fake
    assert loaded.model_name == "patched.pt"


def test_engine_source_does_not_import_ultralytics():
    engine_path = Path(__file__).resolve().parents[1] / "src" / "block_detected" / "runtime" / "engine.py"
    source = engine_path.read_text(encoding="utf-8")

    assert "from ultralytics" not in source
    assert "import ultralytics" not in source


def test_protocols_source_has_no_cv2_or_ultralytics():
    protocols_path = (
        Path(__file__).resolve().parents[1] / "src" / "block_detected" / "core" / "protocols.py"
    )
    source = protocols_path.read_text(encoding="utf-8")

    assert "cv2" not in source
    assert "ultralytics" not in source

"""Engine create/start error messages without camera or weights."""

from pathlib import Path

from block_detected.runtime.config_schema import AppConfig
from block_detected.runtime.engine import WebcamEngine


class _FakeDetector:
    @property
    def model_name(self) -> str:
        return "fake.pt"

    def predict(self, frame, *, conf: float, **kwargs):
        raise AssertionError("not used")

    def close(self) -> None:
        pass


def test_try_create_reports_missing_models_dir(monkeypatch):
    monkeypatch.setattr(
        "block_detected.runtime.engine.discover_model_paths",
        lambda: [],
    )
    engine, error = WebcamEngine.try_create(AppConfig.defaults())
    assert engine is None
    assert error is not None
    assert ".pt" in error
    assert "models" in error.lower()


def test_try_start_reports_camera_index(monkeypatch):
    config = AppConfig.defaults()
    config.camera.index = 7
    engine = WebcamEngine(config, [Path("fake.pt")], _FakeDetector())
    engine.state.camera_index = 7

    monkeypatch.setattr("block_detected.runtime.engine.open_camera", lambda *_a, **_k: None)

    ok, error = engine.try_start()
    assert ok is False
    assert error is not None
    assert "7" in error

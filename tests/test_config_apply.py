"""Tests for hot config application helper."""

from block_detected.runtime.config_apply import (
    apply_hot_runtime_settings,
    config_changed_keys,
    needs_runtime_restart,
)
from block_detected.runtime.config_schema import AppConfig
from block_detected.runtime.engine import WebcamEngine


class _FakeDetector:
    def __init__(self, name: str = "m.pt") -> None:
        self._name = name

    @property
    def model_name(self) -> str:
        return self._name

    def predict(self, frame, *, conf: float):
        raise AssertionError("not used")

    def close(self) -> None:
        pass


def test_apply_hot_runtime_settings_updates_state_and_config():
    config = AppConfig.defaults()
    config.inference.overlay_history = 7
    engine = WebcamEngine(config, [], _FakeDetector())

    apply_hot_runtime_settings(
        engine,
        config,
        confidence=0.42,
        eval_mode=True,
        overlay_enabled=False,
    )

    assert engine.config.inference.overlay_history == 7
    assert engine.state.confidence == 0.42
    assert engine.state.eval_mode is True
    assert engine.state.overlay_enabled is False
    assert engine.state.box_history.maxlen == 7


def test_needs_runtime_restart_for_camera_and_model():
    baseline = AppConfig.defaults()
    current = AppConfig.defaults()
    assert not needs_runtime_restart(current, baseline)

    current.camera.index = 2
    assert needs_runtime_restart(current, baseline)

    current = AppConfig.defaults()
    current.inference.default_model_name = "other.pt"
    assert needs_runtime_restart(current, baseline)

    assert "inference.default_model_name" in config_changed_keys(current, baseline)

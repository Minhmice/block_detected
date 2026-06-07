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
    engine = WebcamEngine(config, [], _FakeDetector())

    apply_hot_runtime_settings(
        engine,
        config,
        confidence=0.42,
        eval_mode=True,
    )

    assert engine.state.confidence == 0.42
    assert engine.state.eval_mode is True


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


def test_config_changed_keys_detects_each_stability_field():
    baseline = AppConfig.defaults()
    fields = {
        "enabled": (True, "stability.enabled"),
        "min_confidence": (0.5, "stability.min_confidence"),
        "min_box_area_px": (100, "stability.min_box_area_px"),
        "reject_edge_boxes": (True, "stability.reject_edge_boxes"),
        "duplicate_merge_iou": (0.8, "stability.duplicate_merge_iou"),
        "temporal_window": (10, "stability.temporal_window"),
        "required_stable_votes": (4, "stability.required_stable_votes"),
    }
    for attr, (value, key) in fields.items():
        current = AppConfig.defaults()
        setattr(current.stability, attr, value)
        changed = config_changed_keys(current, baseline)
        assert key in changed, f"expected {key} for {attr}"


def test_needs_runtime_restart_false_for_stability_only_changes():
    baseline = AppConfig.defaults()
    current = AppConfig.defaults()
    current.stability.enabled = True
    current.stability.min_confidence = 0.25
    current.stability.temporal_window = 8

    assert not needs_runtime_restart(current, baseline)


def test_apply_hot_runtime_settings_updates_stability_config():
    baseline = AppConfig.defaults()
    baseline.stability.enabled = False
    engine = WebcamEngine(baseline, [], _FakeDetector())

    updated = AppConfig.defaults()
    updated.stability.enabled = True

    apply_hot_runtime_settings(
        engine,
        updated,
        confidence=baseline.inference.default_conf,
        eval_mode=False,
    )

    assert engine.config.stability.enabled is True

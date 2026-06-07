"""Unit tests for AppConfig schema, validation, and restart key classification."""

from block_detected.runtime.config_schema import AppConfig


def test_from_dict_partial_camera_section_keeps_other_defaults():
    defaults = AppConfig.defaults()
    config = AppConfig.from_dict({"camera": {"width": 640}})

    assert config.camera.width == 640
    assert config.camera.height == defaults.camera.height
    assert config.camera.index == defaults.camera.index
    assert config.inference.default_conf == defaults.inference.default_conf


def test_from_dict_ignores_unknown_keys_inside_sections():
    defaults = AppConfig.defaults()
    config = AppConfig.from_dict({"camera": {"foo": 1, "width": 800}})

    assert config.camera.width == 800
    assert config.camera.height == defaults.camera.height
    assert not hasattr(config.camera, "foo")


def test_validate_errors_when_required_stable_votes_exceeds_temporal_window():
    config = AppConfig.defaults()
    config.stability.temporal_window = 3
    config.stability.required_stable_votes = 5

    errors = config.validate()

    assert any("required_stable_votes" in e for e in errors)


def test_validate_errors_when_duplicate_merge_iou_out_of_range():
    config = AppConfig.defaults()

    config.stability.duplicate_merge_iou = 0
    errors_zero = config.validate()
    assert any("duplicate_merge_iou" in e for e in errors_zero)

    config.stability.duplicate_merge_iou = 1.5
    errors_high = config.validate()
    assert any("duplicate_merge_iou" in e for e in errors_high)


def test_needs_detector_restart_for_model_name_change():
    assert AppConfig.needs_detector_restart({"inference.default_model_name"})


def test_needs_detector_restart_false_for_stability_keys():
    assert not AppConfig.needs_detector_restart({"stability.enabled"})

"""Tests for AppConfig schema."""

from block_detected.config.schema import AppConfig


def test_defaults():
    defaults = AppConfig.defaults()
    config = AppConfig.from_dict({})
    assert config.camera.width == 640
    assert config.camera.height == defaults.camera.height
    assert config.camera.index == defaults.camera.index
    assert config.inference.default_conf == defaults.inference.default_conf


def test_from_dict_partial_camera():
    config = AppConfig.from_dict({"camera": {"width": 800}})
    assert config.camera.width == 800
    assert config.camera.height == AppConfig.defaults().camera.height
    assert not hasattr(config.camera, "foo")


def test_from_dict_inference_legacy_model_key():
    config = AppConfig.from_dict(
        {"inference": {"default_model_name": "custom.pt", "default_conf": 0.3}}
    )
    assert config.inference.last_model_name == "custom.pt"


def test_from_dict_inference_last_model_name():
    config = AppConfig.from_dict({"inference": {"last_model_name": "custom.pt"}})
    assert config.inference.last_model_name == "custom.pt"


def test_validate_imgsz_multiple_of_32():
    config = AppConfig.defaults()
    config.inference.imgsz = 641
    errors = config.validate()
    assert any("imgsz" in e for e in errors)

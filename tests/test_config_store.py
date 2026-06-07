"""Tests for runtime config load/validate/save."""

from pathlib import Path

from block_detected.runtime.config_schema import AppConfig
from block_detected.runtime.config_store import load_config, save_config, validate_config


def test_defaults_validate():
    config = AppConfig.defaults()
    assert validate_config(config) == []


def test_invalid_conf_range():
    config = AppConfig.defaults()
    config.inference.default_conf = 99.0
    errors = validate_config(config)
    assert any("default_conf" in e for e in errors)


def test_round_trip_toml(tmp_path: Path):
    path = tmp_path / "cfg.toml"
    original = AppConfig.defaults()
    original.inference.default_conf = 0.42
    save_config(original, path)
    loaded = load_config(path)
    assert loaded.inference.default_conf == 0.42


def test_missing_file_uses_defaults(tmp_path: Path):
    loaded = load_config(tmp_path / "missing.toml")
    assert loaded.inference.default_conf == AppConfig.defaults().inference.default_conf


def test_restart_key_classification():
    assert AppConfig.needs_camera_restart({"camera.width"})
    assert not AppConfig.needs_camera_restart({"inference.default_conf"})


def test_invalid_toml_types_return_validation_errors(tmp_path: Path):
    path = tmp_path / "bad.toml"
    path.write_text(
        "\n".join(
            [
                "[camera]",
                'width = "640"',
                "",
                "[inference]",
                'default_conf = "0.3"',
                "",
                "[ui]",
                "log_level = 3",
            ]
        ),
        encoding="utf-8",
    )

    errors = validate_config(load_config(path))

    assert any("camera.width" in error for error in errors)
    assert any("inference.default_conf" in error for error in errors)
    assert any("ui.log_level" in error for error in errors)


def test_load_config_ignores_extra_toml_sections(tmp_path: Path):
    path = tmp_path / "extra.toml"
    path.write_text(
        "\n".join(
            [
                "[camera]",
                "width = 640",
                "",
                "[future]",
                "x = 1",
            ]
        ),
        encoding="utf-8",
    )

    loaded = load_config(path)

    assert loaded.camera.width == 640
    assert validate_config(loaded) == []

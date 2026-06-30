"""Tests for config.paths."""

from block_detected.config.paths import MODELS_DIR, PACKAGE_ROOT, PROJECT_ROOT
from block_detected.config.store import DEFAULT_CONFIG_PATH


def test_project_root_is_repo_root():
    assert (PROJECT_ROOT / "pyproject.toml").is_file()


def test_package_root_is_block_detected_package():
    assert (PACKAGE_ROOT / "config" / "schema.py").is_file()
    assert (PACKAGE_ROOT / "block_detected.json").is_file()


def test_default_config_path_in_package():
    assert DEFAULT_CONFIG_PATH == PACKAGE_ROOT / "block_detected.json"


def test_models_dir_under_project_root():
    assert MODELS_DIR == PROJECT_ROOT / "models"
    assert MODELS_DIR.name == "models"

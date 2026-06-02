"""Tests for config.paths."""

from block_detected.config.paths import MODELS_DIR, PROJECT_ROOT


def test_project_root_is_repo_root():
    assert (PROJECT_ROOT / "pyproject.toml").is_file()


def test_models_dir_under_project_root():
    assert MODELS_DIR == PROJECT_ROOT / "models"
    assert MODELS_DIR.name == "models"

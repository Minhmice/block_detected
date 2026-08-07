"""Filesystem paths for project assets."""

from pathlib import Path

# block_detected/config/paths.py
PACKAGE_ROOT = Path(__file__).resolve().parents[1]
PROJECT_ROOT = Path(__file__).resolve().parents[3]
MODELS_DIR = PROJECT_ROOT / "models"

"""Filesystem paths for project assets."""

from pathlib import Path

# block_detected/config/paths.py → parents[3] = repo root
PROJECT_ROOT = Path(__file__).resolve().parents[3]
MODELS_DIR = PROJECT_ROOT / "models"

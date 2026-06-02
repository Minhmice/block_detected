"""YOLO model discovery and loading."""

from pathlib import Path

from ultralytics import YOLO

from block_detected.config.inference import DEFAULT_MODEL_NAME
from block_detected.config.paths import MODELS_DIR


def discover_model_paths(models_dir: Path = MODELS_DIR) -> list[Path]:
    if not models_dir.is_dir():
        return []
    return sorted(p for p in models_dir.glob("*.pt") if p.is_file())


def default_model_index(model_paths: list[Path], default_name: str = DEFAULT_MODEL_NAME) -> int:
    for index, path in enumerate(model_paths):
        if path.name == default_name:
            return index
    return 0


def load_yolo(model_path: Path) -> YOLO:
    return YOLO(str(model_path))

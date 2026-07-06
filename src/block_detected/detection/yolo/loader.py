"""YOLO model discovery and loading."""

from pathlib import Path

from ultralytics import YOLO

from block_detected.config.inference import DEFAULT_MODEL_NAME
from block_detected.config.paths import MODELS_DIR

# Supported model formats (Ultralytics handles all of these)
SUFFIXES = {".pt", ".onnx", ".engine", ".torchscript"}


def discover_model_paths(models_dir: Path = MODELS_DIR) -> list[Path]:
    if not models_dir.is_dir():
        return []
    models: list[Path] = []
    for suffix in SUFFIXES:
        models.extend(p for p in models_dir.glob(f"*{suffix}") if p.is_file())
    return sorted(set(models))


def resolve_model_index(model_paths: list[Path], preferred_name: str = DEFAULT_MODEL_NAME) -> int:
    for index, path in enumerate(model_paths):
        if path.name == preferred_name:
            return index
    return 0


def default_model_index(model_paths: list[Path], default_name: str = DEFAULT_MODEL_NAME) -> int:
    """Deprecated alias for resolve_model_index."""
    return resolve_model_index(model_paths, preferred_name=default_name)


def load_yolo(model_path: Path) -> YOLO:
    return YOLO(str(model_path))

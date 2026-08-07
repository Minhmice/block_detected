"""YOLO model discovery and loading."""

from __future__ import annotations

import logging
from pathlib import Path

from ultralytics import YOLO

from block_detected.config.inference import DEFAULT_MODEL_NAME
from block_detected.config.paths import MODELS_DIR

logger = logging.getLogger(__name__)

SUFFIXES = {".pt", ".onnx", ".engine", ".torchscript"}


def read_onnx_task(model_path: Path) -> str | None:
    if model_path.suffix.lower() != ".onnx":
        return None
    try:
        import onnx

        model = onnx.load(str(model_path), load_external_data=False)
        for prop in model.metadata_props:
            if prop.key == "task" and prop.value:
                return prop.value
    except Exception as exc:
        logger.debug("Could not read ONNX task metadata for %s: %s", model_path.name, exc)
    return None


def discover_model_paths(models_dir: Path = MODELS_DIR) -> list[Path]:
    if not models_dir.is_dir():
        return []
    models = [
        path
        for suffix in SUFFIXES
        for path in models_dir.glob(f"*{suffix}")
        if path.is_file()
    ]
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
    task = read_onnx_task(model_path)
    if task:
        return YOLO(str(model_path), task=task)
    return YOLO(str(model_path))

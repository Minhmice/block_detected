"""YOLO (Ultralytics) backend."""

from block_detected.detection.yolo.loader import (
    default_model_index,
    discover_model_paths,
    load_yolo,
)

__all__ = ["discover_model_paths", "default_model_index", "load_yolo"]

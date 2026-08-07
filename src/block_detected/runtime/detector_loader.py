"""Load Ultralytics YOLO detector (project default and only backend)."""

from pathlib import Path

from block_detected.core.protocols import DetectorBackend
from block_detected.detection.yolo.backend import YoloDetector


def load_detector(model_path: Path) -> DetectorBackend:
    """Load a YOLO weights file (.pt, .onnx, …) via Ultralytics."""
    return YoloDetector(model_path)

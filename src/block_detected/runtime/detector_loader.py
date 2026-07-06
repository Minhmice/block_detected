"""Load Ultralytics YOLO detector (.pt, .onnx, .engine)."""

from pathlib import Path

from block_detected.core.protocols import DetectorBackend
from block_detected.detection.yolo.backend import YoloDetector


def load_detector(model_path: Path) -> DetectorBackend:
    """Load YOLO model — supports .pt, .onnx, .engine (Ultralytics native)."""
    return YoloDetector(model_path)

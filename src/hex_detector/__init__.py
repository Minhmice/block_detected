"""Hex face geometry detection from YOLO bboxes."""

from .config import DEFAULT_CONFIG, HexDetectorConfig
from .detector import HexDetector
from .models import (
    BBox,
    DetectionMode,
    DetectionResult,
    DetectionSide,
    DetectionStatus,
    HexPoints,
    HexResult,
    LineSegment,
    RejectReason,
    ScoreBreakdown,
    YoloDetection,
)

__all__ = [
    "BBox",
    "DEFAULT_CONFIG",
    "DetectionMode",
    "DetectionResult",
    "DetectionSide",
    "DetectionStatus",
    "HexDetector",
    "HexDetectorConfig",
    "HexPoints",
    "HexResult",
    "LineSegment",
    "RejectReason",
    "ScoreBreakdown",
    "YoloDetection",
]

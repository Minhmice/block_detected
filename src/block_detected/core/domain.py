"""Domain types for detection and runtime (no OpenCV/YOLO imports)."""

from dataclasses import dataclass, field
from typing import Any

from block_detected.core.types import Box


@dataclass(frozen=True, slots=True)
class Detection:
    box: Box
    class_id: int
    class_name: str
    confidence: float


@dataclass(slots=True)
class FrameResult:
    detections: list[Detection]
    raw: Any = None


@dataclass(slots=True)
class InferenceStats:
    fps: float = 0.0
    frame_read_ms: float = 0.0
    inference_ms: float = 0.0
    render_ms: float = 0.0
    model_name: str = ""
    camera_index: int = 0


@dataclass(slots=True)
class RuntimeStatus:
    eval_mode: bool = False
    confidence: float = 0.25
    model_name: str = ""
    camera_index: int = 0
    stability_enabled: bool = False
    detection_count: int = 0
    primary_detection: Detection | None = None
    detections: list[Detection] = field(default_factory=list)
    stats: InferenceStats = field(default_factory=InferenceStats)

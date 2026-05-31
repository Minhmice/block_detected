"""camelCase wire models for frontend contract."""

from __future__ import annotations

from typing import Literal, Optional

from pydantic import BaseModel, ConfigDict, Field, field_validator
from pydantic.alias_generators import to_camel

from app.services.param_utils import coerce_odd_kernel


class _CamelModel(BaseModel):
    model_config = ConfigDict(
        alias_generator=to_camel,
        populate_by_name=True,
        ser_json_by_alias=True,
    )


class PointWire(_CamelModel):
    x: float
    y: float


class CornersWire(_CamelModel):
    tl: PointWire
    tr: PointWire
    br: PointWire
    bl: PointWire


class PickupPoseWire(_CamelModel):
    x_mm: float = Field(serialization_alias="xMm")
    y_mm: float = Field(serialization_alias="yMm")
    theta_deg: float = Field(serialization_alias="thetaDeg")


class DetectionResultWire(_CamelModel):
    block_id: Optional[int] = Field(default=None, serialization_alias="blockId")
    confidence: float = 0.0
    status: str = "no_detection"
    center_px: Optional[PointWire] = Field(default=None, serialization_alias="centerPx")
    corners_px: Optional[CornersWire] = Field(default=None, serialization_alias="cornersPx")
    angle_deg: Optional[float] = Field(default=None, serialization_alias="angleDeg")
    pickup_pose_mm: Optional[PickupPoseWire] = Field(
        default=None, serialization_alias="pickupPoseMm"
    )


class ClassificationScoresWire(_CamelModel):
    block01: float = Field(ge=0.0, le=1.0)
    block02: float = Field(ge=0.0, le=1.0)
    block03: float = Field(ge=0.0, le=1.0)
    block04: float = Field(ge=0.0, le=1.0)


class DetectionTelemetryWire(_CamelModel):
    type: Literal["telemetry"] = "telemetry"
    fps: float = 0.0
    latency_ms: float = Field(default=0.0, serialization_alias="latencyMs")
    valid: bool = False
    reject_reason: Optional[str] = Field(default=None, serialization_alias="rejectReason")
    detection: Optional[DetectionResultWire] = None
    classification_scores: Optional[ClassificationScoresWire] = Field(
        default=None, serialization_alias="classificationScores"
    )


class DetectionParamsWire(_CamelModel):
    blur_kernel: int = Field(default=5, ge=1, le=15)
    adaptive_block_size: int = Field(default=31, ge=3, le=99)
    adaptive_c: int = Field(default=5, ge=0, le=50)
    canny_low: int = Field(default=50, ge=0, le=255)
    canny_high: int = Field(default=150, ge=0, le=255)
    min_area_px: int = Field(default=1000, ge=0, le=200000)
    max_area_px: int = Field(default=80000, ge=0, le=200000)
    aspect_min: float = Field(default=0.75, ge=0.0, le=1.0)
    aspect_max: float = Field(default=1.33, ge=0.0, le=2.0)
    confidence_threshold: float = Field(default=0.5, ge=0.0, le=1.0)

    @field_validator("blur_kernel", mode="before")
    @classmethod
    def _coerce_blur_kernel(cls, value: int) -> int:
        return coerce_odd_kernel(int(value))


class SystemStatusWire(_CamelModel):
    status: str = "ok"
    mock_camera: bool = Field(default=False, serialization_alias="mockCamera")
    detection_running: bool = Field(default=False, serialization_alias="detectionRunning")
    camera_backend: str = Field(default="unknown", serialization_alias="cameraBackend")
    camera_index: int = Field(default=0, serialization_alias="cameraIndex")
    vision_mock_mode: bool = Field(default=True, serialization_alias="visionMockMode")
    ei_model_path: str = Field(default="", serialization_alias="eiModelPath")
    ei_model_loaded: bool = Field(default=False, serialization_alias="eiModelLoaded")
    ei_model_executable: bool = Field(default=False, serialization_alias="eiModelExecutable")
    ei_model_error: Optional[str] = Field(default=None, serialization_alias="eiModelError")
    ei_model_id: str = Field(default="", serialization_alias="eiModelId")
    ei_model_label: str = Field(default="", serialization_alias="eiModelLabel")


class EimModelWire(_CamelModel):
    id: str
    label: str
    path: str
    executable: bool = False


class EimConfigWire(_CamelModel):
    models: list[EimModelWire] = Field(default_factory=list)
    selected_id: str = Field(default="", serialization_alias="selectedId")
    selected_path: str = Field(default="", serialization_alias="selectedPath")
    selected_executable: bool = Field(default=False, serialization_alias="selectedExecutable")
    vision_mock_mode: bool = Field(default=True, serialization_alias="visionMockMode")


class EimConfigUpdateWire(_CamelModel):
    model_id: str = Field(serialization_alias="modelId")


class CameraDeviceWire(_CamelModel):
    index: int
    label: str


class CameraConfigWire(_CamelModel):
    mock_camera: bool = Field(serialization_alias="mockCamera")
    camera_index: int = Field(serialization_alias="cameraIndex")
    available_indices: list[int] = Field(
        default_factory=list, serialization_alias="availableIndices"
    )


class CameraConfigUpdateWire(_CamelModel):
    mock_camera: Optional[bool] = Field(default=None, serialization_alias="mockCamera")
    camera_index: Optional[int] = Field(default=None, serialization_alias="cameraIndex")


class CalibrationSaveWire(_CamelModel):
    table_homography: list[list[float]]
    robot_origin_offset_mm: dict[str, float] = Field(default_factory=dict)
    gripper_offset_mm: dict[str, float] = Field(default_factory=dict)


class DatasetSaveWire(_CamelModel):
    reason: Optional[str] = None

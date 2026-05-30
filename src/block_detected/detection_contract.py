"""Strict output contract for cube block detection results.

This module intentionally contains no image processing code.  It defines the
validated data structures shared by later detection, classification, and robot
pickup modules.
"""

from __future__ import annotations

import json
import math
from dataclasses import dataclass, fields, is_dataclass
from enum import Enum, IntEnum
from numbers import Real
from typing import Any, Dict, Mapping, Optional, Tuple, Type, TypeVar, Union


class DetectionContractError(ValueError):
    """Raised when a detection result violates the output contract."""


class BlockID(IntEnum):
    """Integer enum for the four supported cube block identities."""

    BLOCK_01 = 1
    BLOCK_02 = 2
    BLOCK_03 = 3
    BLOCK_04 = 4


class BlockLabel(str, Enum):
    """String enum for the four supported cube block labels."""

    BLOCK_01 = "block_01"
    BLOCK_02 = "block_02"
    BLOCK_03 = "block_03"
    BLOCK_04 = "block_04"


class DetectionStatus(str, Enum):
    """Classifier and geometry status for one block detection result."""

    OK = "ok"
    LOW_CONFIDENCE = "low_confidence"
    INVALID_GEOMETRY = "invalid_geometry"
    NO_DETECTION = "no_detection"
    MULTIPLE_CANDIDATES = "multiple_candidates"


BLOCK_ID_TO_LABEL: Mapping[BlockID, BlockLabel] = {
    BlockID.BLOCK_01: BlockLabel.BLOCK_01,
    BlockID.BLOCK_02: BlockLabel.BLOCK_02,
    BlockID.BLOCK_03: BlockLabel.BLOCK_03,
    BlockID.BLOCK_04: BlockLabel.BLOCK_04,
}


EnumT = TypeVar("EnumT", bound=Enum)


def _coerce_enum(value: Union[EnumT, str, int], enum_type: Type[EnumT], field_name: str) -> EnumT:
    try:
        return value if isinstance(value, enum_type) else enum_type(value)
    except ValueError as exc:
        allowed = ", ".join(repr(member.value) for member in enum_type)
        raise DetectionContractError(
            f"{field_name} must be one of: {allowed}; got {value!r}"
        ) from exc


def _coerce_optional_enum(
    value: Optional[Union[EnumT, str, int]], enum_type: Type[EnumT], field_name: str
) -> Optional[EnumT]:
    if value is None:
        return None
    return _coerce_enum(value, enum_type, field_name)


def _is_number(value: Any) -> bool:
    return isinstance(value, Real) and not isinstance(value, bool) and math.isfinite(float(value))


def _require_number(value: Any, field_name: str) -> None:
    if not _is_number(value):
        raise DetectionContractError(f"{field_name} must be a finite int or float; got {value!r}")


@dataclass(frozen=True)
class PointPx:
    """A 2D point in image pixel coordinates.

    Attributes:
        x: Horizontal coordinate in pixels.
        y: Vertical coordinate in pixels.
    """

    x: float
    y: float

    def __post_init__(self) -> None:
        _require_number(self.x, "PointPx.x")
        _require_number(self.y, "PointPx.y")


@dataclass(frozen=True)
class CornersPx:
    """Ordered corner points of the detected square face in image pixels.

    Attributes:
        top_left: Corner nearest the top-left of the square face.
        top_right: Corner nearest the top-right of the square face.
        bottom_right: Corner nearest the bottom-right of the square face.
        bottom_left: Corner nearest the bottom-left of the square face.
    """

    top_left: PointPx
    top_right: PointPx
    bottom_right: PointPx
    bottom_left: PointPx

    def __post_init__(self) -> None:
        corners = self.as_ordered_tuple()
        if len(corners) != 4:
            raise DetectionContractError("corners_px must contain exactly 4 points")
        for index, point in enumerate(corners):
            if not isinstance(point, PointPx):
                raise DetectionContractError(
                    f"corners_px point at index {index} must be PointPx; got {type(point).__name__}"
                )

    def as_ordered_tuple(self) -> Tuple[PointPx, PointPx, PointPx, PointPx]:
        """Return corners in top-left, top-right, bottom-right, bottom-left order."""

        return (self.top_left, self.top_right, self.bottom_right, self.bottom_left)


@dataclass(frozen=True)
class BoundingBoxPx:
    """Axis-aligned bounding box around the detected face in image pixels.

    Attributes:
        x: Left edge of the bounding box in pixels.
        y: Top edge of the bounding box in pixels.
        width: Bounding box width in pixels; must be positive.
        height: Bounding box height in pixels; must be positive.
    """

    x: float
    y: float
    width: float
    height: float

    def __post_init__(self) -> None:
        _require_number(self.x, "BoundingBoxPx.x")
        _require_number(self.y, "BoundingBoxPx.y")
        _require_number(self.width, "BoundingBoxPx.width")
        _require_number(self.height, "BoundingBoxPx.height")
        if self.width <= 0.0:
            raise DetectionContractError("bbox_px.width must be positive")
        if self.height <= 0.0:
            raise DetectionContractError("bbox_px.height must be positive")


@dataclass(frozen=True)
class PickupPose:
    """Robot pickup pose derived from camera geometry.

    Attributes:
        x_mm: Pickup target x coordinate in robot/world millimeters.
        y_mm: Pickup target y coordinate in robot/world millimeters.
        theta_deg: End-effector yaw angle in degrees.
    """

    x_mm: float
    y_mm: float
    theta_deg: float

    def __post_init__(self) -> None:
        _require_number(self.x_mm, "PickupPose.x_mm")
        _require_number(self.y_mm, "PickupPose.y_mm")
        _require_number(self.theta_deg, "PickupPose.theta_deg")


@dataclass(frozen=True)
class DebugInfo:
    """Optional diagnostics for tuning and logging.

    Attributes:
        frame_id: Optional camera frame identifier used for tracing.
        method: Optional name of the detector/classifier method that produced the result.
        rejection_reason: Optional reason a candidate was rejected or downgraded.
        raw_score: Optional unnormalized detector/classifier score.
    """

    frame_id: Optional[str] = None
    method: Optional[str] = None
    rejection_reason: Optional[str] = None
    raw_score: Optional[float] = None

    def __post_init__(self) -> None:
        if self.frame_id is not None and not isinstance(self.frame_id, str):
            raise DetectionContractError("debug.frame_id must be a string when provided")
        if self.method is not None and not isinstance(self.method, str):
            raise DetectionContractError("debug.method must be a string when provided")
        if self.rejection_reason is not None and not isinstance(self.rejection_reason, str):
            raise DetectionContractError("debug.rejection_reason must be a string when provided")
        if self.raw_score is not None:
            _require_number(self.raw_score, "debug.raw_score")


@dataclass(frozen=True)
class DetectionResult:
    """Validated output object for a single block detection attempt.

    Attributes:
        block_id: Integer block identity enum, allowed values 1 through 4.
            Use ``None`` only when no valid single block candidate exists.
        label: String block label enum, allowed values ``block_01`` through
            ``block_04``.  When present, it must match ``block_id``.
        confidence: Normalized confidence score from 0.0 to 1.0.
        center_px: Center point of the detected square face in image pixels.
            Use ``None`` only when no valid single block candidate exists.
        corners_px: Exactly four ordered corner points of the face:
            top_left, top_right, bottom_right, bottom_left.  Use ``None`` only
            when no valid single block candidate exists.
        angle_deg: Rotation angle of the detected square face in image space.
            Use ``None`` only when no valid single block candidate exists.
        bbox_px: Axis-aligned pixel bounding box around the detected face.
            Use ``None`` only when no valid single block candidate exists.
        face_area_px: Pixel area of the detected square face.  Use ``None``
            only when no valid single block candidate exists.
        pickup_pose: Optional robot pickup pose.  This is expected to be
            ``None`` until later pose-calculation stages populate it.
        status: Detection status enum: ok, low_confidence, invalid_geometry,
            no_detection, or multiple_candidates.
        debug: Optional diagnostics for logs, tuning, and rejected candidates.
    """

    block_id: Optional[BlockID]
    label: Optional[BlockLabel]
    confidence: float
    center_px: Optional[PointPx]
    corners_px: Optional[CornersPx]
    angle_deg: Optional[float]
    bbox_px: Optional[BoundingBoxPx]
    face_area_px: Optional[float]
    pickup_pose: Optional[PickupPose]
    status: DetectionStatus
    debug: Optional[DebugInfo] = None

    def __post_init__(self) -> None:
        object.__setattr__(
            self, "block_id", _coerce_optional_enum(self.block_id, BlockID, "block_id")
        )
        object.__setattr__(
            self, "label", _coerce_optional_enum(self.label, BlockLabel, "label")
        )
        object.__setattr__(self, "status", _coerce_enum(self.status, DetectionStatus, "status"))
        _validate_detection_result_fields(self)


def _validate_detection_result_fields(result: DetectionResult) -> None:
    _require_number(result.confidence, "confidence")
    if not 0.0 <= float(result.confidence) <= 1.0:
        raise DetectionContractError("confidence must be between 0.0 and 1.0")

    if (result.block_id is None) != (result.label is None):
        raise DetectionContractError("block_id and label must either both be set or both be None")

    if result.block_id is not None and BLOCK_ID_TO_LABEL[result.block_id] != result.label:
        expected_label = BLOCK_ID_TO_LABEL[result.block_id].value
        raise DetectionContractError(
            f"block_id {int(result.block_id)} must use label {expected_label!r}; "
            f"got {result.label.value!r}"
        )

    if result.center_px is not None and not isinstance(result.center_px, PointPx):
        raise DetectionContractError("center_px must be PointPx when provided")
    if result.corners_px is not None and not isinstance(result.corners_px, CornersPx):
        raise DetectionContractError("corners_px must be CornersPx when provided")
    if result.bbox_px is not None and not isinstance(result.bbox_px, BoundingBoxPx):
        raise DetectionContractError("bbox_px must be BoundingBoxPx when provided")
    if result.pickup_pose is not None and not isinstance(result.pickup_pose, PickupPose):
        raise DetectionContractError("pickup_pose must be PickupPose or None")
    if result.debug is not None and not isinstance(result.debug, DebugInfo):
        raise DetectionContractError("debug must be DebugInfo or None")
    if result.angle_deg is not None:
        _require_number(result.angle_deg, "angle_deg")
    if result.face_area_px is not None:
        _require_number(result.face_area_px, "face_area_px")
        if result.face_area_px < 0.0:
            raise DetectionContractError("face_area_px must be non-negative")

    candidate_fields = (
        result.block_id,
        result.label,
        result.center_px,
        result.corners_px,
        result.angle_deg,
        result.bbox_px,
        result.face_area_px,
    )

    if result.status in {DetectionStatus.OK, DetectionStatus.LOW_CONFIDENCE}:
        if any(value is None for value in candidate_fields):
            raise DetectionContractError(
                f"status {result.status.value!r} requires block identity and geometry fields"
            )
    elif result.status in {
        DetectionStatus.NO_DETECTION,
        DetectionStatus.INVALID_GEOMETRY,
        DetectionStatus.MULTIPLE_CANDIDATES,
    }:
        if any(value is not None for value in candidate_fields):
            raise DetectionContractError(
                f"status {result.status.value!r} must not include a valid block candidate"
            )
        if result.pickup_pose is not None:
            raise DetectionContractError(
                f"status {result.status.value!r} must use pickup_pose=None"
            )
        if result.debug is None or not result.debug.rejection_reason:
            raise DetectionContractError(
                f"status {result.status.value!r} requires debug.rejection_reason"
            )


def make_no_detection_result(
    *,
    frame_id: Optional[str] = None,
    method: Optional[str] = None,
    rejection_reason: str = "no block candidate detected",
    raw_score: Optional[float] = None,
) -> DetectionResult:
    """Create a valid no-detection result with nullable candidate fields.

    Args:
        frame_id: Optional camera frame identifier for debug tracing.
        method: Optional detector method name for debug tracing.
        rejection_reason: Explanation stored in ``debug.rejection_reason``.
        raw_score: Optional raw detector score, if one exists.

    Returns:
        A ``DetectionResult`` with ``status=NO_DETECTION`` and confidence 0.0.
    """

    return DetectionResult(
        block_id=None,
        label=None,
        confidence=0.0,
        center_px=None,
        corners_px=None,
        angle_deg=None,
        bbox_px=None,
        face_area_px=None,
        pickup_pose=None,
        status=DetectionStatus.NO_DETECTION,
        debug=DebugInfo(
            frame_id=frame_id,
            method=method,
            rejection_reason=rejection_reason,
            raw_score=raw_score,
        ),
    )


def make_multiple_candidates_result(
    *,
    frame_id: Optional[str] = None,
    method: Optional[str] = None,
    rejection_reason: str = "multiple block candidates detected",
    raw_score: Optional[float] = None,
) -> DetectionResult:
    """Create a valid ambiguous-scene result with no single block candidate."""

    return DetectionResult(
        block_id=None,
        label=None,
        confidence=0.0,
        center_px=None,
        corners_px=None,
        angle_deg=None,
        bbox_px=None,
        face_area_px=None,
        pickup_pose=None,
        status=DetectionStatus.MULTIPLE_CANDIDATES,
        debug=DebugInfo(
            frame_id=frame_id,
            method=method,
            rejection_reason=rejection_reason,
            raw_score=raw_score,
        ),
    )


def validate_detection_result(result: DetectionResult) -> DetectionResult:
    """Validate a detection result and return it unchanged.

    Args:
        result: Detection result dataclass instance to validate.

    Returns:
        The same ``DetectionResult`` instance when valid.

    Raises:
        DetectionContractError: If any field violates the contract.
    """

    if not isinstance(result, DetectionResult):
        raise DetectionContractError(
            f"result must be DetectionResult; got {type(result).__name__}"
        )
    _validate_detection_result_fields(result)
    return result


def _to_json_compatible(value: Any) -> Any:
    if isinstance(value, IntEnum):
        return int(value)
    if isinstance(value, Enum):
        return value.value
    if is_dataclass(value):
        return {field.name: _to_json_compatible(getattr(value, field.name)) for field in fields(value)}
    if isinstance(value, Mapping):
        return {key: _to_json_compatible(item) for key, item in value.items()}
    if isinstance(value, tuple) or isinstance(value, list):
        return [_to_json_compatible(item) for item in value]
    return value


def result_to_dict(result: DetectionResult) -> Dict[str, Any]:
    """Convert a valid detection result to a JSON-compatible dictionary."""

    validate_detection_result(result)
    return _to_json_compatible(result)


def result_to_json(result: DetectionResult) -> str:
    """Serialize a valid detection result to a JSON string.

    Args:
        result: Validated detection result to serialize.

    Returns:
        A deterministic, indented JSON string using enum values.
    """

    return json.dumps(result_to_dict(result), indent=2, sort_keys=False)


SAMPLE_SUCCESS_BLOCK_1 = DetectionResult(
    block_id=BlockID.BLOCK_01,
    label=BlockLabel.BLOCK_01,
    confidence=0.94,
    center_px=PointPx(x=321.5, y=244.0),
    corners_px=CornersPx(
        top_left=PointPx(x=280.0, y=203.0),
        top_right=PointPx(x=362.0, y=205.5),
        bottom_right=PointPx(x=359.5, y=286.0),
        bottom_left=PointPx(x=278.0, y=283.0),
    ),
    angle_deg=1.8,
    bbox_px=BoundingBoxPx(x=278.0, y=203.0, width=84.0, height=83.0),
    face_area_px=6724.0,
    pickup_pose=None,
    status=DetectionStatus.OK,
    debug=DebugInfo(frame_id="frame_000123", method="contract_sample", raw_score=0.981),
)


SAMPLE_LOW_CONFIDENCE = DetectionResult(
    block_id=BlockID.BLOCK_02,
    label=BlockLabel.BLOCK_02,
    confidence=0.42,
    center_px=PointPx(x=198.0, y=180.5),
    corners_px=CornersPx(
        top_left=PointPx(x=160.0, y=142.0),
        top_right=PointPx(x=235.0, y=146.0),
        bottom_right=PointPx(x=232.0, y=220.0),
        bottom_left=PointPx(x=156.5, y=216.0),
    ),
    angle_deg=3.1,
    bbox_px=BoundingBoxPx(x=156.5, y=142.0, width=78.5, height=78.0),
    face_area_px=5776.0,
    pickup_pose=None,
    status=DetectionStatus.LOW_CONFIDENCE,
    debug=DebugInfo(
        frame_id="frame_000124",
        method="contract_sample",
        rejection_reason="classification confidence below pickup threshold",
        raw_score=0.42,
    ),
)


SAMPLE_NO_DETECTION = make_no_detection_result(
    frame_id="frame_000125",
    method="contract_sample",
)


SAMPLE_OUTPUTS_JSON: Mapping[str, str] = {
    "successful_detection_block_1": result_to_json(SAMPLE_SUCCESS_BLOCK_1),
    "low_confidence_detection": result_to_json(SAMPLE_LOW_CONFIDENCE),
    "no_detection": result_to_json(SAMPLE_NO_DETECTION),
}

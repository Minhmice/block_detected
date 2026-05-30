"""Block detection package — contract boundary and pipeline skeleton."""

from .detection_contract import (
    BLOCK_ID_TO_LABEL,
    SAMPLE_LOW_CONFIDENCE,
    SAMPLE_NO_DETECTION,
    SAMPLE_OUTPUTS_JSON,
    SAMPLE_SUCCESS_BLOCK_1,
    BlockID,
    BlockLabel,
    BoundingBoxPx,
    CornersPx,
    DebugInfo,
    DetectionContractError,
    DetectionResult,
    DetectionStatus,
    PickupPose,
    PointPx,
    make_multiple_candidates_result,
    make_no_detection_result,
    result_to_dict,
    result_to_json,
    validate_detection_result,
)
from .pipeline import detect_block

__version__ = "0.1.0"

__all__ = [
    "BLOCK_ID_TO_LABEL",
    "BlockID",
    "BlockLabel",
    "BoundingBoxPx",
    "CornersPx",
    "DebugInfo",
    "DetectionContractError",
    "DetectionResult",
    "DetectionStatus",
    "PickupPose",
    "PointPx",
    "SAMPLE_LOW_CONFIDENCE",
    "SAMPLE_NO_DETECTION",
    "SAMPLE_OUTPUTS_JSON",
    "SAMPLE_SUCCESS_BLOCK_1",
    "__version__",
    "detect_block",
    "make_multiple_candidates_result",
    "make_no_detection_result",
    "result_to_dict",
    "result_to_json",
    "validate_detection_result",
]

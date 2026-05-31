"""Stable mock vision detections for dev machines without aarch64 EIM."""

from __future__ import annotations

import time
from typing import Optional

import numpy as np

from block_detected.camera import CaptureFrame, TARGET_SHAPE
from block_detected.detection_contract import (
    BLOCK_ID_TO_LABEL,
    BlockID,
    BoundingBoxPx,
    CornersPx,
    DebugInfo,
    DetectionResult,
    DetectionStatus,
    PointPx,
    validate_detection_result,
)
from block_detected.pipeline import PipelineSettings, _capture_from_frame

_METHOD = "vision_mock_v1"

_MOCK_SCORES: dict[str, float] = {
    "block_01": 0.02,
    "block_02": 0.92,
    "block_03": 0.03,
    "block_04": 0.03,
}


def _frame_id(frame: object) -> str:
    capture = _capture_from_frame(frame)
    if capture is not None:
        return capture.frame_id
    return "frame_mock"


def detect_from_frame(
    frame: object,
    *,
    settings: Optional[PipelineSettings] = None,
) -> tuple[DetectionResult, dict[str, float]]:
    del settings
    capture = _capture_from_frame(frame)
    if capture is None and isinstance(frame, np.ndarray):
        if frame.shape == TARGET_SHAPE and frame.dtype == np.uint8:
            capture = CaptureFrame(
                frame_id="frame_mock",
                image_bgr=frame,
                timestamp_ns=time.time_ns(),
                source="ndarray",
            )
    frame_id = capture.frame_id if capture else _frame_id(frame)

    corners = CornersPx(
        top_left=PointPx(x=260.0, y=180.0),
        top_right=PointPx(x=380.0, y=180.0),
        bottom_right=PointPx(x=380.0, y=300.0),
        bottom_left=PointPx(x=260.0, y=300.0),
    )
    result = validate_detection_result(
        DetectionResult(
            block_id=BlockID.BLOCK_02,
            label=BLOCK_ID_TO_LABEL[BlockID.BLOCK_02],
            confidence=0.92,
            center_px=PointPx(x=320.0, y=240.0),
            corners_px=corners,
            angle_deg=0.0,
            bbox_px=BoundingBoxPx(x=260.0, y=180.0, width=120.0, height=120.0),
            face_area_px=14400.0,
            pickup_pose=None,
            status=DetectionStatus.OK,
            debug=DebugInfo(frame_id=frame_id, method=_METHOD, raw_score=0.92),
        )
    )
    return result, dict(_MOCK_SCORES)

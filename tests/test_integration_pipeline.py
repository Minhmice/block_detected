"""End-to-end detect_block integration (Phase 7/8)."""

from __future__ import annotations

import json
import time

import cv2
import numpy as np

from block_detected.camera import CaptureFrame
from block_detected.detection_contract import DetectionStatus
from block_detected.pipeline import detect_block
from block_detected.detection_contract import result_to_json, validate_detection_result


def _square_frame() -> np.ndarray:
    frame = np.zeros((480, 640, 3), dtype=np.uint8)
    cv2.rectangle(frame, (260, 180), (380, 300), (235, 235, 235), -1)
    return frame


def test_detect_block_finds_square_face() -> None:
    capture = CaptureFrame(
        frame_id="frame_int",
        image_bgr=_square_frame(),
        timestamp_ns=time.time_ns(),
        source="test",
    )
    result = detect_block(capture)
    validate_detection_result(result)
    assert result.status in {DetectionStatus.OK, DetectionStatus.LOW_CONFIDENCE}
    assert result.corners_px is not None
    assert result.center_px is not None
    assert result.angle_deg is not None


def test_detect_block_no_detection_on_blank() -> None:
    blank = np.zeros((480, 640, 3), dtype=np.uint8)
    result = detect_block(blank)
    assert result.status == DetectionStatus.NO_DETECTION


def test_detect_block_json_roundtrip() -> None:
    result = detect_block(_square_frame())
    payload = json.loads(result_to_json(result))
    assert "status" in payload
    assert payload["status"] in ("ok", "low_confidence")

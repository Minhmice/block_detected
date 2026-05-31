"""Tests for vision mock detections."""

from __future__ import annotations

import numpy as np

from app.services.vision_mock import detect_from_frame
from block_detected.detection_contract import BlockID, validate_detection_result


def test_mock_stable_block() -> None:
    frame = np.zeros((480, 640, 3), dtype=np.uint8)
    result_a, scores_a = detect_from_frame(frame)
    result_b, scores_b = detect_from_frame(frame)
    validate_detection_result(result_a)
    assert result_a.block_id == BlockID.BLOCK_02
    assert result_b.block_id == BlockID.BLOCK_02
    assert result_a.corners_px == result_b.corners_px
    assert scores_a == scores_b


def test_mock_scores_sum_near_one() -> None:
    frame = np.zeros((480, 640, 3), dtype=np.uint8)
    _, scores = detect_from_frame(frame)
    assert 0.99 <= sum(scores.values()) <= 1.01


def test_mock_validate_contract() -> None:
    frame = np.zeros((480, 640, 3), dtype=np.uint8)
    result, _ = detect_from_frame(frame)
    validate_detection_result(result)

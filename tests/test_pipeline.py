"""Public API tests for detect_block(frame)."""

from __future__ import annotations

import unittest

from block_detected import detect_block
from block_detected import (
    DetectionResult,
    DetectionStatus,
    result_to_dict,
    validate_detection_result,
)


class DetectBlockPipelineTests(unittest.TestCase):
    def test_ordinary_frame_returns_no_detection(self) -> None:
        result = detect_block({"frame_id": "ordinary"})
        self.assertIs(validate_detection_result(result), result)
        self.assertEqual(result.status, DetectionStatus.NO_DETECTION)
        self.assertEqual(result.confidence, 0.0)
        self.assertIsNone(result.block_id)
        self.assertIsNone(result.center_px)
        self.assertIsNone(result.corners_px)
        self.assertIsNone(result.angle_deg)
        self.assertIsNone(result.bbox_px)
        self.assertIsNone(result.face_area_px)
        self.assertIsNone(result.pickup_pose)
        self.assertIsNotNone(result.debug)
        self.assertTrue(result.debug.rejection_reason)

    def test_synthetic_success_populates_geometry(self) -> None:
        result = detect_block(
            {"__block_detected_synthetic__": "success_block_1", "frame_id": "synthetic"}
        )
        self.assertEqual(result.status, DetectionStatus.OK)
        self.assertIsNotNone(result.block_id)
        self.assertIsNotNone(result.label)
        self.assertGreater(result.confidence, 0.0)
        self.assertIsNotNone(result.center_px)
        corners = result.corners_px
        self.assertIsNotNone(corners)
        self.assertIsNotNone(corners.top_left)
        self.assertIsNotNone(corners.top_right)
        self.assertIsNotNone(corners.bottom_right)
        self.assertIsNotNone(corners.bottom_left)
        self.assertIsNotNone(result.angle_deg)

    def test_synthetic_multiple_candidates_no_geometry(self) -> None:
        result = detect_block(
            {"__block_detected_synthetic__": "multiple_candidates", "frame_id": "ambiguous"}
        )
        self.assertEqual(result.status, DetectionStatus.MULTIPLE_CANDIDATES)
        self.assertIsNone(result.block_id)
        self.assertIsNone(result.center_px)
        self.assertIsNone(result.corners_px)
        self.assertIsNone(result.pickup_pose)
        self.assertIsNotNone(result.debug)
        self.assertTrue(result.debug.rejection_reason)

    def test_result_serializes_to_dict(self) -> None:
        result = detect_block(object())
        payload = result_to_dict(result)
        self.assertEqual(payload["status"], "no_detection")


if __name__ == "__main__":
    unittest.main()

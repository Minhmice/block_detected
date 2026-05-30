"""Regression tests for detection contract validation."""

from __future__ import annotations

import unittest

from block_detected.detection_contract import (
    BlockID,
    BlockLabel,
    DebugInfo,
    DetectionContractError,
    DetectionResult,
    DetectionStatus,
    make_multiple_candidates_result,
    result_to_json,
    validate_detection_result,
)
from block_detected.detection_contract import (
    SAMPLE_LOW_CONFIDENCE,
    SAMPLE_NO_DETECTION,
    SAMPLE_SUCCESS_BLOCK_1,
)


class DetectionContractTests(unittest.TestCase):
    def test_sample_success_validates_and_serializes(self) -> None:
        result = validate_detection_result(SAMPLE_SUCCESS_BLOCK_1)
        payload = result_to_json(result)
        self.assertIn('"block_id": 1', payload)
        self.assertIn('"status": "ok"', payload)

    def test_sample_no_detection_has_nullable_geometry(self) -> None:
        result = validate_detection_result(SAMPLE_NO_DETECTION)
        self.assertIsNone(result.block_id)
        self.assertIsNone(result.center_px)
        self.assertIsNotNone(result.debug)
        self.assertTrue(result.debug.rejection_reason)

    def test_block_id_label_mismatch_raises(self) -> None:
        with self.assertRaises(DetectionContractError):
            DetectionResult(
                block_id=BlockID.BLOCK_01,
                label=BlockLabel.BLOCK_02,
                confidence=0.5,
                center_px=SAMPLE_SUCCESS_BLOCK_1.center_px,
                corners_px=SAMPLE_SUCCESS_BLOCK_1.corners_px,
                angle_deg=0.0,
                bbox_px=SAMPLE_SUCCESS_BLOCK_1.bbox_px,
                face_area_px=100.0,
                pickup_pose=None,
                status=DetectionStatus.OK,
            )

    def test_multiple_candidates_no_geometry_validates(self) -> None:
        result = make_multiple_candidates_result(
            frame_id="ambiguous",
            method="test",
        )
        validated = validate_detection_result(result)
        self.assertEqual(validated.status, DetectionStatus.MULTIPLE_CANDIDATES)
        self.assertIsNone(validated.block_id)
        self.assertIsNone(validated.corners_px)

    def test_multiple_candidates_with_geometry_raises(self) -> None:
        with self.assertRaises(DetectionContractError):
            DetectionResult(
                block_id=BlockID.BLOCK_01,
                label=BlockLabel.BLOCK_01,
                confidence=0.0,
                center_px=SAMPLE_SUCCESS_BLOCK_1.center_px,
                corners_px=SAMPLE_SUCCESS_BLOCK_1.corners_px,
                angle_deg=0.0,
                bbox_px=SAMPLE_SUCCESS_BLOCK_1.bbox_px,
                face_area_px=1.0,
                pickup_pose=None,
                status=DetectionStatus.MULTIPLE_CANDIDATES,
                debug=DebugInfo(rejection_reason="multiple candidates with geometry"),
            )

    def test_low_confidence_sample_still_validates(self) -> None:
        validate_detection_result(SAMPLE_LOW_CONFIDENCE)


if __name__ == "__main__":
    unittest.main()

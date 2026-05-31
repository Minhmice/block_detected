"""Edge Impulse Linux .eim inference with geometry pre-step."""

from __future__ import annotations

from pathlib import Path
from typing import Optional

import cv2
import numpy as np

from block_detected.camera import CaptureFrame

from block_detected.calibration import pixel_to_pickup_pose
from block_detected.detection_contract import (
    BLOCK_ID_TO_LABEL,
    BlockID,
    DebugInfo,
    DetectionResult,
    DetectionStatus,
    make_multiple_candidates_result,
    make_no_detection_result,
    validate_detection_result,
)
from block_detected.geometry import geometry_from_candidate, validate_quad_geometry
from block_detected.pipeline import (
    PipelineSettings,
    _bbox_from_corners,
    _capture_from_frame,
    _multiple_candidates,
    _string_frame_id,
)
from block_detected.vision import find_square_candidates_from_frame

from app.services.eim_model import resolve_eim_path, validate_eim_model

_METHOD = "edge_impulse_v1"

_LABEL_TO_BLOCK_ID: dict[str, BlockID] = {
    "block_01": BlockID.BLOCK_01,
    "block_02": BlockID.BLOCK_02,
    "block_03": BlockID.BLOCK_03,
    "block_04": BlockID.BLOCK_04,
    "1": BlockID.BLOCK_01,
    "2": BlockID.BLOCK_02,
    "3": BlockID.BLOCK_03,
    "4": BlockID.BLOCK_04,
    "class0": BlockID.BLOCK_01,
    "class1": BlockID.BLOCK_02,
    "class2": BlockID.BLOCK_03,
    "class3": BlockID.BLOCK_04,
}


def _normalize_scores(classification: dict) -> dict[str, float]:
    scores: dict[str, float] = {
        "block_01": 0.0,
        "block_02": 0.0,
        "block_03": 0.0,
        "block_04": 0.0,
    }
    for label, prob in classification.items():
        key = str(label).strip().lower()
        block_id = _LABEL_TO_BLOCK_ID.get(key)
        if block_id is None:
            continue
        field = f"block_{block_id.value:02d}"
        scores[field] = max(scores[field], float(prob))
    total = sum(scores.values())
    if total > 0:
        scores = {k: v / total for k, v in scores.items()}
    return scores


def _map_ei_classification(
    classification: dict,
    *,
    min_confidence: float,
) -> tuple[Optional[BlockID], float, dict[str, float], Optional[str]]:
    scores = _normalize_scores(classification)
    if not any(scores.values()):
        return None, 0.0, scores, "unknown Edge Impulse classification labels"

    best_label = max(scores, key=scores.get)
    confidence = scores[best_label]
    block_id = BlockID(int(best_label.split("_")[1]))
    if confidence < min_confidence:
        return block_id, confidence, scores, "classification confidence below pickup threshold"
    return block_id, confidence, scores, None


class EdgeImpulseRunnerService:
    def __init__(self, *, min_confidence: float = 0.5) -> None:
        self._runner = None
        self._initialized = False
        self._min_confidence = min_confidence

    @property
    def initialized(self) -> bool:
        return self._initialized

    def reload(self) -> None:
        if self._runner is not None:
            stop = getattr(self._runner, "stop", None)
            if callable(stop):
                try:
                    stop()
                except Exception:
                    pass
        self._runner = None
        self._initialized = False

    def ensure_initialized(self) -> None:
        if self._initialized:
            return
        status = validate_eim_model()
        if not status.executable:
            raise RuntimeError(status.error or "EIM model not ready")
        from edge_impulse_linux.image import ImageImpulseRunner

        self._runner = ImageImpulseRunner(str(status.path))
        self._runner.init()
        self._initialized = True

    def classify_warped_bgr(
        self,
        warped_bgr: np.ndarray,
    ) -> tuple[Optional[BlockID], float, dict[str, float], Optional[str]]:
        self.ensure_initialized()
        rgb = cv2.cvtColor(warped_bgr, cv2.COLOR_BGR2RGB)
        features, _ = self._runner.get_features_from_image(rgb)
        ei_result = self._runner.classify(features)
        classification = ei_result.get("result", {}).get("classification", {})
        return _map_ei_classification(classification, min_confidence=self._min_confidence)

    def detect_block_types_in_frame(
        self,
        frame: object,
        settings: PipelineSettings,
    ) -> set[int]:
        capture = _capture_from_frame(frame)
        if capture is None:
            return set()

        found = find_square_candidates_from_frame(capture, settings.vision)
        image = capture.image_bgr
        height, width = image.shape[:2]
        legend_max_y = height * 0.25
        column_width = width // 4
        by_quadrant: dict[int, list] = {0: [], 1: [], 2: [], 3: []}

        for candidate in found.candidates:
            x, y, w, h = candidate.bbox_xywh
            center_x = x + w / 2.0
            center_y = y + h / 2.0
            if center_y < legend_max_y:
                continue
            quadrant = min(3, int(center_x // column_width))
            by_quadrant[quadrant].append(candidate)

        detected: set[int] = set()
        min_area = settings.min_face_area_px * 0.25

        for index in range(4):
            candidates = by_quadrant[index]
            if not candidates:
                continue
            candidate = max(candidates, key=lambda item: item.area_px)
            if candidate.area_px < min_area:
                continue
            geom = geometry_from_candidate(candidate, image)
            if not validate_quad_geometry(geom.corners_px):
                continue
            block_id, _, _, reject_reason = self.classify_warped_bgr(geom.warped_bgr)
            if block_id is not None and reject_reason is None:
                detected.add(int(block_id.value))

        return detected

    def detect_from_frame(
        self,
        frame: object,
        settings: PipelineSettings,
    ) -> tuple[DetectionResult, dict[str, float]]:
        self.ensure_initialized()
        frame_id = _string_frame_id(frame)

        capture = _capture_from_frame(frame)
        if capture is None:
            result = validate_detection_result(
                make_no_detection_result(
                    frame_id=frame_id,
                    method=_METHOD,
                    rejection_reason="unsupported frame input; expected CaptureFrame or 480×640 uint8 BGR",
                )
            )
            return result, {"block_01": 0.25, "block_02": 0.25, "block_03": 0.25, "block_04": 0.25}

        found = find_square_candidates_from_frame(capture, settings.vision)
        frame_id = found.frame_id

        if not found.candidates:
            result = validate_detection_result(
                make_no_detection_result(
                    frame_id=frame_id,
                    method=_METHOD,
                    rejection_reason="no square-face contour passed geometry filters",
                )
            )
            return result, {"block_01": 0.25, "block_02": 0.25, "block_03": 0.25, "block_04": 0.25}

        if _multiple_candidates(found.candidates, settings):
            result = validate_detection_result(
                make_multiple_candidates_result(
                    frame_id=frame_id,
                    method=_METHOD,
                    rejection_reason="multiple square-face candidates with similar scores",
                    raw_score=float(found.candidates[0].score),
                )
            )
            return result, {"block_01": 0.25, "block_02": 0.25, "block_03": 0.25, "block_04": 0.25}

        candidate = found.candidates[0]
        if candidate.area_px < settings.min_face_area_px:
            result = validate_detection_result(
                make_no_detection_result(
                    frame_id=frame_id,
                    method=_METHOD,
                    rejection_reason="face area below minimum pixel threshold",
                    raw_score=float(candidate.area_px),
                )
            )
            return result, {"block_01": 0.25, "block_02": 0.25, "block_03": 0.25, "block_04": 0.25}

        geom = geometry_from_candidate(candidate, capture.image_bgr)
        if not validate_quad_geometry(geom.corners_px):
            result = validate_detection_result(
                DetectionResult(
                    block_id=None,
                    label=None,
                    confidence=0.0,
                    center_px=None,
                    corners_px=None,
                    angle_deg=None,
                    bbox_px=None,
                    face_area_px=None,
                    pickup_pose=None,
                    status=DetectionStatus.INVALID_GEOMETRY,
                    debug=DebugInfo(
                        frame_id=frame_id,
                        method=_METHOD,
                        rejection_reason="quad corner angles outside square-face bounds",
                        raw_score=float(candidate.score),
                    ),
                )
            )
            return result, {"block_01": 0.25, "block_02": 0.25, "block_03": 0.25, "block_04": 0.25}

        rgb = cv2.cvtColor(geom.warped_bgr, cv2.COLOR_BGR2RGB)
        features, _ = self._runner.get_features_from_image(rgb)
        ei_result = self._runner.classify(features)
        classification = ei_result.get("result", {}).get("classification", {})
        block_id, confidence, scores, reject_reason = _map_ei_classification(
            classification,
            min_confidence=self._min_confidence,
        )

        if block_id is None:
            result = validate_detection_result(
                make_no_detection_result(
                    frame_id=frame_id,
                    method=_METHOD,
                    rejection_reason=reject_reason or "Edge Impulse returned no labels",
                )
            )
            return result, scores

        status = (
            DetectionStatus.OK
            if reject_reason is None
            else DetectionStatus.LOW_CONFIDENCE
        )
        pickup = pixel_to_pickup_pose(
            geom.center_px,
            geom.angle_deg,
            settings.calibration,
        )
        result = validate_detection_result(
            DetectionResult(
                block_id=block_id,
                label=BLOCK_ID_TO_LABEL[block_id],
                confidence=confidence,
                center_px=geom.center_px,
                corners_px=geom.corners_px,
                angle_deg=geom.angle_deg,
                bbox_px=_bbox_from_corners(geom.corners_px),
                face_area_px=float(candidate.area_px),
                pickup_pose=pickup,
                status=status,
                debug=DebugInfo(
                    frame_id=frame_id,
                    method=_METHOD,
                    rejection_reason=reject_reason,
                    raw_score=confidence,
                ),
            )
        )
        return result, scores


ei_runner_service = EdgeImpulseRunnerService()

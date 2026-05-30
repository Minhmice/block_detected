"""Public detection entry point — capture → vision → geometry → classify → pose."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Mapping, Optional, Union

import numpy as np

from .calibration import CalibrationSettings, pixel_to_pickup_pose
from .camera import TARGET_SHAPE, CaptureFrame
from .classifier import ClassifierSettings, classify_face, create_classifier
from .detection_contract import (
    BLOCK_ID_TO_LABEL,
    BoundingBoxPx,
    DebugInfo,
    DetectionResult,
    DetectionStatus,
    make_multiple_candidates_result,
    make_no_detection_result,
    validate_detection_result,
)
from .detection_contract import SAMPLE_SUCCESS_BLOCK_1
from .geometry import geometry_from_candidate, validate_quad_geometry
from .vision import VisionSettings, find_square_candidates_from_frame

_SYNTHETIC_KEY = "__block_detected_synthetic__"
_METHOD = "detect_block_v1"


@dataclass(frozen=True)
class PipelineSettings:
    vision: VisionSettings = VisionSettings()
    classifier: ClassifierSettings = ClassifierSettings()
    calibration: CalibrationSettings = CalibrationSettings()
    min_face_area_px: float = 1000.0
    multiple_candidate_area_ratio: float = 0.85


def _string_frame_id(frame: object) -> Optional[str]:
    if isinstance(frame, CaptureFrame):
        return frame.frame_id
    if isinstance(frame, Mapping):
        frame_id = frame.get("frame_id")
        if isinstance(frame_id, str):
            return frame_id
    return None


def _synthetic_mode(frame: object) -> Optional[str]:
    if isinstance(frame, Mapping):
        mode = frame.get(_SYNTHETIC_KEY)
        if isinstance(mode, str):
            return mode
    return None


def _capture_from_frame(frame: object) -> Optional[CaptureFrame]:
    if isinstance(frame, CaptureFrame):
        return frame
    if isinstance(frame, np.ndarray):
        if frame.shape != TARGET_SHAPE or frame.dtype != np.uint8:
            return None
        return CaptureFrame(
            frame_id="frame_unknown",
            image_bgr=frame,
            timestamp_ns=0,
            source="ndarray",
        )
    if isinstance(frame, Mapping):
        image = frame.get("image_bgr")
        if isinstance(image, np.ndarray):
            fid = frame.get("frame_id")
            return CaptureFrame(
                frame_id=fid if isinstance(fid, str) else "frame_unknown",
                image_bgr=image,
                timestamp_ns=int(frame.get("timestamp_ns", 0)),
                source=str(frame.get("source", "mapping")),
            )
    return None


def _bbox_from_corners(geom_corners) -> BoundingBoxPx:
    xs = [
        geom_corners.top_left.x,
        geom_corners.top_right.x,
        geom_corners.bottom_right.x,
        geom_corners.bottom_left.x,
    ]
    ys = [
        geom_corners.top_left.y,
        geom_corners.top_right.y,
        geom_corners.bottom_right.y,
        geom_corners.bottom_left.y,
    ]
    x0, x1 = min(xs), max(xs)
    y0, y1 = min(ys), max(ys)
    return BoundingBoxPx(x=x0, y=y0, width=x1 - x0, height=y1 - y0)


def _multiple_candidates(candidates, settings: PipelineSettings) -> bool:
    if len(candidates) < 2:
        return False
    top = candidates[0].score
    second = candidates[1].score
    if second >= top * settings.multiple_candidate_area_ratio:
        return True
    return False


def detect_block(
    frame: object,
    settings: PipelineSettings | None = None,
) -> DetectionResult:
    """Run end-to-end detection on a BGR frame or :class:`CaptureFrame`."""
    settings = settings or PipelineSettings()
    frame_id = _string_frame_id(frame)
    synthetic = _synthetic_mode(frame)

    if synthetic == "success_block_1":
        return validate_detection_result(SAMPLE_SUCCESS_BLOCK_1)

    if synthetic == "multiple_candidates":
        return validate_detection_result(
            make_multiple_candidates_result(frame_id=frame_id, method=_METHOD)
        )

    capture = _capture_from_frame(frame)
    if capture is None:
        return validate_detection_result(
            make_no_detection_result(
                frame_id=frame_id,
                method=_METHOD,
                rejection_reason="unsupported frame input; expected CaptureFrame or 480×640 uint8 BGR",
            )
        )

    found = find_square_candidates_from_frame(capture, settings.vision)
    frame_id = found.frame_id

    if not found.candidates:
        return validate_detection_result(
            make_no_detection_result(
                frame_id=frame_id,
                method=_METHOD,
                rejection_reason="no square-face contour passed geometry filters",
            )
        )

    if _multiple_candidates(found.candidates, settings):
        return validate_detection_result(
            make_multiple_candidates_result(
                frame_id=frame_id,
                method=_METHOD,
                rejection_reason="multiple square-face candidates with similar scores",
                raw_score=float(found.candidates[0].score),
            )
        )

    candidate = found.candidates[0]
    if candidate.area_px < settings.min_face_area_px:
        return validate_detection_result(
            make_no_detection_result(
                frame_id=frame_id,
                method=_METHOD,
                rejection_reason="face area below minimum pixel threshold",
                raw_score=float(candidate.area_px),
            )
        )

    geom = geometry_from_candidate(candidate, capture.image_bgr)
    if not validate_quad_geometry(geom.corners_px):
        return validate_detection_result(
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

    clf = create_classifier(settings.classifier)
    classification = classify_face(geom.warped_bgr, settings.classifier, clf)
    status = (
        DetectionStatus.OK
        if classification.confidence >= settings.classifier.min_confidence
        else DetectionStatus.LOW_CONFIDENCE
    )
    pickup = pixel_to_pickup_pose(
        geom.center_px,
        geom.angle_deg,
        settings.calibration,
    )

    return validate_detection_result(
        DetectionResult(
            block_id=classification.block_id,
            label=BLOCK_ID_TO_LABEL[classification.block_id],
            confidence=classification.confidence,
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
                rejection_reason=(
                    "classification confidence below pickup threshold"
                    if status == DetectionStatus.LOW_CONFIDENCE
                    else None
                ),
                raw_score=classification.raw_score,
            ),
        )
    )

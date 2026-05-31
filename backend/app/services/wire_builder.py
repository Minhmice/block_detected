"""Convert detection_contract results to camelCase wire telemetry."""

from __future__ import annotations

from typing import Optional

from block_detected.detection_contract import (
    CornersPx,
    DetectionResult,
    DetectionStatus,
    PickupPose,
    PointPx,
)

from app.schemas.wire import (
    ClassificationScoresWire,
    CornersWire,
    DetectionResultWire,
    DetectionTelemetryWire,
    PickupPoseWire,
    PointWire,
)


def _point_wire(p: PointPx) -> PointWire:
    return PointWire(x=float(p.x), y=float(p.y))


def _corners_wire(corners: CornersPx) -> CornersWire:
    return CornersWire(
        tl=_point_wire(corners.top_left),
        tr=_point_wire(corners.top_right),
        br=_point_wire(corners.bottom_right),
        bl=_point_wire(corners.bottom_left),
    )


def _pickup_wire(pose: PickupPose) -> PickupPoseWire:
    return PickupPoseWire(
        x_mm=float(pose.x_mm),
        y_mm=float(pose.y_mm),
        theta_deg=float(pose.theta_deg),
    )


def detection_result_from_contract(result: DetectionResult) -> DetectionResultWire:
    block_id = int(result.block_id) if result.block_id is not None else None
    center = _point_wire(result.center_px) if result.center_px else None
    corners = _corners_wire(result.corners_px) if result.corners_px else None
    pickup = _pickup_wire(result.pickup_pose) if result.pickup_pose else None
    return DetectionResultWire(
        block_id=block_id,
        confidence=float(result.confidence),
        status=result.status.value,
        center_px=center,
        corners_px=corners,
        angle_deg=float(result.angle_deg) if result.angle_deg is not None else None,
        pickup_pose_mm=pickup,
    )


def classification_scores_from_classifier(
    scores: Optional[dict[str, float]],
) -> ClassificationScoresWire:
    # TODO: wire classifier softmax when exposed
    if scores is None:
        return ClassificationScoresWire(block01=0.25, block02=0.25, block03=0.25, block04=0.25)
    normalized = {k.lower(): float(v) for k, v in scores.items()}
    return ClassificationScoresWire(
        block01=normalized.get("block01", normalized.get("block_01", 0.25)),
        block02=normalized.get("block02", normalized.get("block_02", 0.25)),
        block03=normalized.get("block03", normalized.get("block_03", 0.25)),
        block04=normalized.get("block04", normalized.get("block_04", 0.25)),
    )


def build_telemetry_from_contract(
    result: DetectionResult,
    *,
    fps: float,
    latency_ms: float,
    classifier_scores: Optional[dict[str, float]] = None,
) -> DetectionTelemetryWire:
    valid = result.status == DetectionStatus.OK
    reject_reason = None
    if result.debug and result.debug.rejection_reason:
        reject_reason = result.debug.rejection_reason
    elif not valid:
        reject_reason = result.status.value

    return DetectionTelemetryWire(
        fps=fps,
        latency_ms=latency_ms,
        valid=valid,
        reject_reason=reject_reason,
        detection=detection_result_from_contract(result),
        classification_scores=classification_scores_from_classifier(classifier_scores),
    )

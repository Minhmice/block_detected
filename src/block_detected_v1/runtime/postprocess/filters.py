"""Spatial detection filters."""

from block_detected.core.domain import Detection
from block_detected.vision.geometry import box_area, iou

DEFAULT_EDGE_MARGIN_PX = 2


def filter_min_confidence(detections: list[Detection], min_confidence: float) -> list[Detection]:
    if min_confidence <= 0:
        return list(detections)
    return [d for d in detections if d.confidence >= min_confidence]


def filter_min_area(detections: list[Detection], min_area_px: int) -> list[Detection]:
    if min_area_px <= 0:
        return list(detections)
    return [d for d in detections if box_area(d.box) >= min_area_px]


def filter_edge_boxes(
    detections: list[Detection],
    *,
    frame_width: int,
    frame_height: int,
    margin_px: int = DEFAULT_EDGE_MARGIN_PX,
) -> list[Detection]:
    if frame_width < 1 or frame_height < 1:
        return list(detections)
    kept: list[Detection] = []
    for detection in detections:
        x1, y1, x2, y2 = detection.box
        touches_edge = (
            x1 <= margin_px
            or y1 <= margin_px
            or x2 >= frame_width - margin_px
            or y2 >= frame_height - margin_px
        )
        if not touches_edge:
            kept.append(detection)
    return kept


def merge_duplicate_detections(
    detections: list[Detection],
    *,
    iou_threshold: float,
) -> list[Detection]:
    if iou_threshold <= 0 or len(detections) < 2:
        return list(detections)

    ordered = sorted(detections, key=lambda d: d.confidence, reverse=True)
    kept: list[Detection] = []
    for candidate in ordered:
        if any(
            candidate.class_id == existing.class_id
            and iou(candidate.box, existing.box) >= iou_threshold
            for existing in kept
        ):
            continue
        kept.append(candidate)
    return kept

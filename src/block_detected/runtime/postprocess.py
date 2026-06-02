"""Detection post-processing: spatial filters, duplicate merge, temporal stability."""

from __future__ import annotations

from collections import deque
from dataclasses import dataclass

from block_detected.core.domain import Detection
from block_detected.core.types import Box
from block_detected.runtime.config_schema import StabilityConfig
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


def _detection_matches(detection: Detection, other: Detection, match_iou: float) -> bool:
    return detection.class_id == other.class_id and iou(detection.box, other.box) >= match_iou


@dataclass
class TemporalStabilityTracker:
    """Keep detections that appear in enough recent frames (vote over a sliding window)."""

    window: int
    required_votes: int
    match_iou: float
    _history: deque[list[Detection]] | None = None

    def __post_init__(self) -> None:
        self.reset()

    def reset(self) -> None:
        size = max(1, self.window)
        self._history = deque(maxlen=size)

    def update(self, detections: list[Detection]) -> list[Detection]:
        if self._history is None:
            self.reset()
        assert self._history is not None
        self._history.append(list(detections))

        stable: list[Detection] = []
        for detection in detections:
            votes = sum(
                1
                for frame_detections in self._history
                if any(_detection_matches(detection, other, self.match_iou) for other in frame_detections)
            )
            if votes >= self.required_votes:
                stable.append(detection)
        return stable


class DetectionPostProcessor:
    """Apply stability config to per-frame detections."""

    def __init__(self, config: StabilityConfig) -> None:
        self._config = config
        self._tracker = self._build_tracker(config)

    def _build_tracker(self, config: StabilityConfig) -> TemporalStabilityTracker:
        return TemporalStabilityTracker(
            window=max(1, config.temporal_window),
            required_votes=max(1, min(config.required_stable_votes, config.temporal_window)),
            match_iou=config.duplicate_merge_iou,
        )

    def update_config(self, config: StabilityConfig) -> None:
        tracker_keys = (
            config.temporal_window,
            config.required_stable_votes,
            config.duplicate_merge_iou,
        )
        previous_keys = (
            self._config.temporal_window,
            self._config.required_stable_votes,
            self._config.duplicate_merge_iou,
        )
        self._config = config
        if tracker_keys != previous_keys:
            self._tracker = self._build_tracker(config)
        elif not config.enabled:
            self.reset()

    def reset(self) -> None:
        self._tracker.reset()

    def process(
        self,
        detections: list[Detection],
        *,
        frame_width: int,
        frame_height: int,
    ) -> list[Detection]:
        if not self._config.enabled:
            return list(detections)

        filtered = filter_min_confidence(detections, self._config.min_confidence)
        filtered = filter_min_area(filtered, self._config.min_box_area_px)
        if self._config.reject_edge_boxes:
            filtered = filter_edge_boxes(
                filtered,
                frame_width=frame_width,
                frame_height=frame_height,
            )
        filtered = merge_duplicate_detections(
            filtered,
            iou_threshold=self._config.duplicate_merge_iou,
        )
        return self._tracker.update(filtered)

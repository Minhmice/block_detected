"""Orchestrate spatial filters and temporal stability."""

from block_detected.config.schema import StabilityConfig
from block_detected.core.domain import Detection
from block_detected.runtime.postprocess.filters import (
    filter_edge_boxes,
    filter_min_area,
    filter_min_confidence,
    merge_duplicate_detections,
)
from block_detected.runtime.postprocess.temporal import TemporalStabilityTracker


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

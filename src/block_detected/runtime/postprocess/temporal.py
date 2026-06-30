"""Temporal stability over detection history."""

from __future__ import annotations

from collections import deque
from dataclasses import dataclass

from block_detected.core.domain import Detection
from block_detected.vision.geometry import iou


def _detection_matches(detection: Detection, other: Detection, match_iou: float) -> bool:
    return detection.class_id == other.class_id and iou(detection.box, other.box) >= match_iou


@dataclass
class TemporalStabilityTracker:
    """Keep detections that appear in enough recent frames."""

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

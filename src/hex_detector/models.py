"""Data models for hex detection."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Literal

import numpy as np
from numpy.typing import NDArray

PointName = Literal["A", "B", "C", "D", "E", "F"]
DetectionMode = Literal["hex", "rectangle", "not_detected"]
DetectionStatus = Literal["detected", "held", "rejected"]
RejectReason = Literal[
    "NO_LINES",
    "NO_FRONT_FACE",
    "INVALID_TOPOLOGY",
    "LOW_EDGE_SUPPORT",
    "LOW_SCORE",
    "ROI_EMPTY",
]
FloatArray = NDArray[np.float64]


@dataclass(frozen=True)
class ScoreBreakdown:
    edge_support: float
    parallelism: float
    topology: float
    area_position: float
    temporal: float
    total: float

    def to_dict(self) -> dict[str, float]:
        return {
            "edge_support": self.edge_support,
            "parallelism": self.parallelism,
            "topology": self.topology,
            "area_position": self.area_position,
            "temporal": self.temporal,
            "total": self.total,
        }


@dataclass(frozen=True)
class BBox:
    x1: float
    y1: float
    x2: float
    y2: float

    def width(self) -> float:
        return max(0.0, self.x2 - self.x1)

    def height(self) -> float:
        return max(0.0, self.y2 - self.y1)

    def area(self) -> float:
        return self.width() * self.height()

    def clamp(self, frame_w: int, frame_h: int) -> BBox:
        return BBox(
            x1=float(np.clip(self.x1, 0, frame_w - 1)),
            y1=float(np.clip(self.y1, 0, frame_h - 1)),
            x2=float(np.clip(self.x2, 0, frame_w - 1)),
            y2=float(np.clip(self.y2, 0, frame_h - 1)),
        )

    def pad(self, ratio: float) -> BBox:
        w, h = self.width(), self.height()
        px, py = w * ratio, h * ratio
        return BBox(self.x1 - px, self.y1 - py, self.x2 + px, self.y2 + py)

    def as_int_tuple(self) -> tuple[int, int, int, int]:
        return int(self.x1), int(self.y1), int(self.x2), int(self.y2)

    def to_dict(self) -> dict[str, float]:
        return {"x1": self.x1, "y1": self.y1, "x2": self.x2, "y2": self.y2}


@dataclass(frozen=True)
class YoloDetection:
    track_id: int
    bbox: BBox
    confidence: float


@dataclass(frozen=True)
class LineSegment:
    x1: float
    y1: float
    x2: float
    y2: float
    group: str = "unknown"

    def length(self) -> float:
        return float(np.hypot(self.x2 - self.x1, self.y2 - self.y1))

    def angle_deg(self) -> float:
        """Direction angle in [0, 180)."""
        ang = float(np.degrees(np.arctan2(self.y2 - self.y1, self.x2 - self.x1)))
        if ang < 0:
            ang += 180.0
        return ang

    def midpoint(self) -> tuple[float, float]:
        return (self.x1 + self.x2) / 2.0, (self.y1 + self.y2) / 2.0

    def to_array(self) -> FloatArray:
        return np.array([self.x1, self.y1, self.x2, self.y2], dtype=np.float64)


@dataclass
class HexPoints:
    A: tuple[float, float] | None = None
    B: tuple[float, float] | None = None
    C: tuple[float, float] | None = None
    D: tuple[float, float] | None = None
    E: tuple[float, float] | None = None
    F: tuple[float, float] | None = None

    def as_dict(self) -> dict[str, tuple[float, float] | None]:
        return {
            "A": self.A,
            "B": self.B,
            "C": self.C,
            "D": self.D,
            "E": self.E,
            "F": self.F,
        }

    def filled_for_mode(self, mode: DetectionMode) -> dict[str, tuple[float, float] | None]:
        d = self.as_dict()
        if mode == "rectangle":
            d["C"] = None
            d["D"] = None
        return d


@dataclass
class DetectionResult:
    track_id: int
    mode: DetectionMode
    points: dict[str, tuple[float, float] | None]
    score: float
    roi_bbox: dict[str, float]
    reject_reason: str = ""
    debug: dict[str, object] = field(default_factory=dict)
    status: DetectionStatus = "detected"
    score_breakdown: ScoreBreakdown | None = None

    def to_dict(self) -> dict[str, object]:
        d: dict[str, object] = {
            "track_id": self.track_id,
            "mode": self.mode,
            "points": self.points,
            "score": self.score,
            "roi_bbox": self.roi_bbox,
            "reject_reason": self.reject_reason,
            "status": self.status,
        }
        if self.score_breakdown is not None:
            d["score_breakdown"] = self.score_breakdown.to_dict()
        return d


# Compatibility alias
HexResult = DetectionResult


@dataclass
class LineGroups:
    vertical: list[LineSegment] = field(default_factory=list)
    front_horizontal: list[LineSegment] = field(default_factory=list)
    right_diagonal: list[LineSegment] = field(default_factory=list)

    def all_lines(self) -> list[LineSegment]:
        return self.vertical + self.front_horizontal + self.right_diagonal

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple

Point = Tuple[float, float]


@dataclass
class Point2D:
    x: float
    y: float

    def as_tuple(self) -> Point:
        return (self.x, self.y)

    def as_list(self) -> List[float]:
        return [self.x, self.y]


@dataclass
class HexagonDetection:
    points: Dict[str, Point2D]
    contour_area: float
    score: float = 1.0


@dataclass
class BlockResult:
    points: Dict[str, Point2D]
    center: Point2D
    front_width: float
    right_width: float
    yaw_deg: float
    score: float
    geometry: Optional["GeometryResult"] = None


@dataclass
class GeometryResult:
    front_face: List[Point2D]
    right_face: List[Point2D]
    front_width: float
    right_width: float
    yaw_deg: float
    center: Point2D
    front_split_lines: List[Tuple[Point, Point]] = field(default_factory=list)
    right_split_lines: List[Tuple[Point, Point]] = field(default_factory=list)
    block_lines: List[Tuple[Point, Point]] = field(default_factory=list)

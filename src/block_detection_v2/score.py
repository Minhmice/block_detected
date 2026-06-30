from __future__ import annotations

import math
from typing import Dict, List, Tuple

import numpy as np

from . import config
from .models import Point2D
from .roi import ROIBox

Point = Tuple[float, float]
LABELS = "ABCDEF"


def _polygon_area(pts: List[Point]) -> float:
    if len(pts) < 3:
        return 0.0
    arr = np.array(pts, dtype=np.float64)
    x, y = arr[:, 0], arr[:, 1]
    return float(0.5 * abs(np.dot(x, np.roll(y, -1)) - np.dot(y, np.roll(x, -1))))


def _dist(a: Point, b: Point) -> float:
    return math.hypot(a[0] - b[0], a[1] - b[1])


def validate_topology(points: Dict[str, Point2D], *, strict: bool = False) -> bool:
    a, b, c, d, e, f = (points[k].as_tuple() for k in LABELS)
    if not (a[0] < b[0] < c[0] and f[0] < e[0] < d[0]):
        return False
    top_y = (a[1] + b[1] + c[1]) / 3.0
    bot_y = (d[1] + e[1] + f[1]) / 3.0
    if top_y >= bot_y - 15:
        return False
    if strict and e[1] < top_y + (bot_y - top_y) * 0.25:
        return False
    if _polygon_area([a, b, c, d, e, f]) < 2000:
        return False
    return True


def edge_support(points: Dict[str, Point2D], edges: np.ndarray, sample_step: int = 4) -> float:
    order = ["A", "B", "C", "D", "E", "F", "A"]
    hits = 0
    total = 0
    h, w = edges.shape[:2]
    for i in range(6):
        p1 = points[order[i]].as_tuple()
        p2 = points[order[i + 1]].as_tuple()
        length = _dist(p1, p2)
        steps = max(2, int(length / sample_step))
        for t in range(steps + 1):
            x = int(p1[0] + (p2[0] - p1[0]) * t / steps)
            y = int(p1[1] + (p2[1] - p1[1]) * t / steps)
            if 0 <= x < w and 0 <= y < h:
                total += 1
                patch = edges[max(0, y - 2) : y + 3, max(0, x - 2) : x + 3]
                if patch.size and patch.max() > 0:
                    hits += 1
    return hits / max(total, 1)


def score_candidate(
    points: Dict[str, Point2D],
    edges: np.ndarray,
    roi: ROIBox,
    *,
    strict_topology: bool = True,
) -> float:
    pts = [points[k].as_tuple() for k in LABELS]
    hex_area = _polygon_area(pts)
    roi_area = max(roi.area, 1)
    area_ratio = min(1.0, hex_area / roi_area)
    support = edge_support(points, edges)
    topo = 1.0 if validate_topology(points, strict=strict_topology) else 0.0

    if hex_area < config.SCORE_HEX_AREA_MIN:
        return 0.0
    if area_ratio < config.SCORE_AREA_RATIO_MIN:
        return 0.0

    return float(
        config.SCORE_WEIGHT_AREA * area_ratio
        + config.SCORE_WEIGHT_EDGE * support
        + config.SCORE_WEIGHT_TOPO * topo
    )

from __future__ import annotations

"""Legacy contour-based hexagon detection. Primary path is pipeline.detect_raw_hexagons."""
import math
from typing import Dict, List, Optional, Tuple

import cv2
import numpy as np

from . import config
from .models import HexagonDetection, Point2D

Point = Tuple[float, float]


def _dist(a: Point, b: Point) -> float:
    return math.hypot(a[0] - b[0], a[1] - b[1])


def _polygon_area(pts: List[Point]) -> float:
    if len(pts) < 3:
        return 0.0
    arr = np.array(pts, dtype=np.float64)
    x = arr[:, 0]
    y = arr[:, 1]
    return float(0.5 * abs(np.dot(x, np.roll(y, -1)) - np.dot(y, np.roll(x, -1))))


def _segments_intersect(p1: Point, p2: Point, p3: Point, p4: Point) -> bool:
    def orient(a: Point, b: Point, c: Point) -> float:
        return (b[0] - a[0]) * (c[1] - a[1]) - (b[1] - a[1]) * (c[0] - a[0])

    def on_segment(a: Point, b: Point, c: Point) -> bool:
        return (
            min(a[0], c[0]) <= b[0] <= max(a[0], c[0])
            and min(a[1], c[1]) <= b[1] <= max(a[1], c[1])
        )

    o1 = orient(p1, p2, p3)
    o2 = orient(p1, p2, p4)
    o3 = orient(p3, p4, p1)
    o4 = orient(p3, p4, p2)

    if o1 * o2 < 0 and o3 * o4 < 0:
        return True
    if o1 == 0 and on_segment(p1, p3, p2):
        return True
    if o2 == 0 and on_segment(p1, p4, p2):
        return True
    if o3 == 0 and on_segment(p3, p1, p4):
        return True
    if o4 == 0 and on_segment(p3, p2, p4):
        return True
    return False


def _is_self_intersecting(pts: List[Point]) -> bool:
    n = len(pts)
    if n < 4:
        return False
    for i in range(n):
        a1 = pts[i]
        a2 = pts[(i + 1) % n]
        for j in range(i + 1, n):
            if abs(i - j) <= 1 or (i == 0 and j == n - 1):
                continue
            b1 = pts[j]
            b2 = pts[(j + 1) % n]
            if _segments_intersect(a1, a2, b1, b2):
                return True
    return False


def _near_convex(pts: List[Point]) -> bool:
    arr = np.array(pts, dtype=np.float32).reshape(-1, 1, 2)
    hull = cv2.convexHull(arr)
    hull_area = cv2.contourArea(hull)
    poly_area = _polygon_area(pts)
    if hull_area <= 1.0:
        return False
    return (poly_area / hull_area) >= (1.0 - config.CONVEXITY_TOLERANCE)


def _order_hexagon(pts: List[Point]) -> Optional[Dict[str, Point2D]]:
    if len(pts) != 6:
        return None

    ys = [p[1] for p in pts]
    mid_y = (min(ys) + max(ys)) / 2.0
    top = sorted([p for p in pts if p[1] <= mid_y], key=lambda p: p[0])
    bottom = sorted([p for p in pts if p[1] > mid_y], key=lambda p: p[0])

    if len(top) != 3 or len(bottom) != 3:
        top = sorted(pts, key=lambda p: (p[1], p[0]))[:3]
        bottom = sorted(pts, key=lambda p: (p[1], p[0]), reverse=True)[:3]
        top = sorted(top, key=lambda p: p[0])
        bottom = sorted(bottom, key=lambda p: p[0])

    if len(top) != 3 or len(bottom) != 3:
        return None

    a, b, c = top[0], top[1], top[2]
    f, e, d = bottom[0], bottom[1], bottom[2]

    top_y = sum(p[1] for p in top) / 3.0
    bottom_y = sum(p[1] for p in bottom) / 3.0
    if top_y >= bottom_y - 10:
        return None

    ordered = [a, b, c, d, e, f]
    if _is_self_intersecting(ordered):
        return None

    front = [a, b, e, f]
    right = [b, c, d, e]
    if _polygon_area(front) < config.MIN_FACE_AREA:
        return None
    if _polygon_area(right) < config.MIN_FACE_AREA:
        return None

    return {
        "A": Point2D(a[0], a[1]),
        "B": Point2D(b[0], b[1]),
        "C": Point2D(c[0], c[1]),
        "D": Point2D(d[0], d[1]),
        "E": Point2D(e[0], e[1]),
        "F": Point2D(f[0], f[1]),
    }

def _detection_score(pts: List[Point], ordered: Dict[str, Point2D], area: float) -> float:
    arr = np.array(pts, dtype=np.float32).reshape(-1, 1, 2)
    hull = cv2.convexHull(arr)
    hull_area = max(cv2.contourArea(hull), 1.0)
    convex_ratio = _polygon_area(pts) / hull_area

    a = ordered["A"].as_tuple()
    b = ordered["B"].as_tuple()
    c = ordered["C"].as_tuple()
    d = ordered["D"].as_tuple()
    e = ordered["E"].as_tuple()
    f = ordered["F"].as_tuple()
    front = _polygon_area([a, b, e, f])
    right = _polygon_area([b, c, d, e])
    face_ratio = min(front, right) / max(area, 1.0)

    top_y = (a[1] + b[1] + c[1]) / 3.0
    bottom_y = (d[1] + e[1] + f[1]) / 3.0
    row_sep = min(1.0, max(0.0, (bottom_y - top_y) / max(_frame_height_hint(pts), 1.0)))

    return float(0.45 * convex_ratio + 0.4 * min(face_ratio * 4.0, 1.0) + 0.15 * row_sep)


def _frame_height_hint(pts: List[Point]) -> float:
    ys = [p[1] for p in pts]
    return max(ys) - min(ys)


def _center_of(points: Dict[str, Point2D]) -> Point:
    cx = sum(p.x for p in points.values()) / 6.0
    cy = sum(p.y for p in points.values()) / 6.0
    return (cx, cy)


def _too_close(centers: List[Point], c: Point) -> bool:
    for other in centers:
        if _dist(other, c) < config.MIN_BLOCK_CENTER_DIST:
            return True
    return False


def _contour_to_points(cnt: np.ndarray, epsilon_ratio: float) -> List[Point]:
    peri = cv2.arcLength(cnt, True)
    approx = cv2.approxPolyDP(cnt, epsilon_ratio * peri, True)
    return [(float(p[0][0]), float(p[0][1])) for p in approx]


def _collect_candidates(contours) -> List[HexagonDetection]:
    candidates: List[HexagonDetection] = []

    for cnt in contours:
        area = cv2.contourArea(cnt)
        if area < config.MIN_CONTOUR_AREA:
            continue

        for ratio in (
            config.POLYGON_EPSILON_RATIO,
            config.POLYGON_EPSILON_RATIO * 0.5,
            config.POLYGON_EPSILON_RATIO * 0.7,
            config.POLYGON_EPSILON_RATIO * 1.3,
            config.POLYGON_EPSILON_RATIO * 1.6,
        ):
            pts = _contour_to_points(cnt, ratio)
            if len(pts) != 6:
                continue
            if not _near_convex(pts):
                continue
            ordered = _order_hexagon(pts)
            if ordered is None:
                continue
            score = _detection_score(pts, ordered, area)
            if score < config.DETECTION_SCORE_MIN:
                continue
            candidates.append(HexagonDetection(points=ordered, contour_area=area, score=score))

    return candidates


def find_hexagons(edges: np.ndarray, frame_shape: tuple[int, int]) -> List[HexagonDetection]:
    contours, _ = cv2.findContours(edges, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    raw = _collect_candidates(contours)
    if not raw:
        contours, _ = cv2.findContours(edges, cv2.RETR_LIST, cv2.CHAIN_APPROX_SIMPLE)
        raw = _collect_candidates(contours)

    raw.sort(key=lambda d: d.score, reverse=True)

    picked: List[HexagonDetection] = []
    centers: List[Point] = []
    for det in raw:
        c = _center_of(det.points)
        if _too_close(centers, c):
            continue
        centers.append(c)
        picked.append(det)
        if len(picked) >= config.MAX_BLOCKS:
            break
    return picked


def find_hexagon(edges: np.ndarray, frame_shape: tuple[int, int]) -> Optional[HexagonDetection]:
    blocks = find_hexagons(edges, frame_shape)
    return blocks[0] if blocks else None

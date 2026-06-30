from __future__ import annotations

import math
from dataclasses import dataclass
from typing import Dict, List, Optional, Tuple

from . import config
from .edges import LineSegment
from .models import Point2D
from .roi import ROIBox

Point = Tuple[float, float]
LineABC = Tuple[float, float, float]  # ax + by = c
LABELS = "ABCDEF"


@dataclass(frozen=True)
class HexFormula:
    """Parameters for the standard isometric trapezoid hex A–F."""

    theta_top_deg: float
    theta_side_deg: float
    split_frac: float
    top_line: LineABC
    bottom_line: LineABC
    left_line: LineABC
    right_line: LineABC
    vertices: Dict[str, Point2D]

    def as_dict(self) -> dict:
        def _line_dict(line: LineABC) -> dict:
            a, b, c = line
            return {"a": a, "b": b, "c": c}

        return {
            "theta_top_deg": self.theta_top_deg,
            "theta_side_deg": self.theta_side_deg,
            "split_frac": self.split_frac,
            "lines": {
                "top": _line_dict(self.top_line),
                "bottom": _line_dict(self.bottom_line),
                "left": _line_dict(self.left_line),
                "right": _line_dict(self.right_line),
            },
            "vertices": {k: [v.x, v.y] for k, v in self.vertices.items()},
            "constraints": {
                "A_B_C_collinear": "top line",
                "F_E_D_collinear": "bottom line",
                "top_parallel_bottom": True,
                "left_parallel_right": True,
                "B_frac_from_A_to_C": self.split_frac,
                "E_frac_from_F_to_D": self.split_frac,
            },
        }


def _line_angle(p1: Point, p2: Point) -> float:
    return math.degrees(math.atan2(p2[1] - p1[1], p2[0] - p1[0])) % 180.0


def _line_length(p1: Point, p2: Point) -> float:
    return math.hypot(p2[0] - p1[0], p2[1] - p1[1])


def _merge_lines_by_angle(
    lines: List[LineSegment],
    angle_tol: float = 12.0,
    min_len: float = 25.0,
) -> List[LineSegment]:
    buckets: Dict[int, List[LineSegment]] = {}
    for p1, p2 in lines:
        length = _line_length(p1, p2)
        if length < min_len:
            continue
        angle = _line_angle(p1, p2)
        key = int(round(angle / angle_tol))
        buckets.setdefault(key, []).append((p1, p2))

    merged: List[LineSegment] = []
    for segs in buckets.values():
        pts = [p for seg in segs for p in seg]
        xs = [p[0] for p in pts]
        ys = [p[1] for p in pts]
        merged.append(((min(xs), min(ys)), (max(xs), max(ys))))
    return merged


def _dominant_angles(lines: List[LineSegment], bins: int = 18) -> List[float]:
    if not lines:
        return []
    hist = [0.0] * bins
    for p1, p2 in lines:
        ang = _line_angle(p1, p2)
        bucket = int(ang / (180.0 / bins)) % bins
        hist[bucket] += _line_length(p1, p2)
    peaks: List[tuple[float, float]] = []
    for i, weight in enumerate(hist):
        left = hist[(i - 1) % bins]
        right = hist[(i + 1) % bins]
        if weight >= left and weight >= right and weight > 0:
            peaks.append((i * (180.0 / bins) + (180.0 / bins) / 2.0, weight))
    peaks.sort(key=lambda x: x[1], reverse=True)
    return [p[0] for p in peaks[:4]]


def _pick_line_near_angle(lines: List[LineSegment], target_deg: float, tol: float = 25.0) -> Optional[LineSegment]:
    best = None
    best_d = 999.0
    for seg in lines:
        ang = _line_angle(seg[0], seg[1])
        d = min(abs(ang - target_deg), abs(ang - target_deg - 180))
        if d < tol and d < best_d:
            best_d = d
            best = seg
    return best


def _line_from_angle_point(pt: Point, angle_deg: float) -> LineABC:
    rad = math.radians(angle_deg)
    dx, dy = math.cos(rad), math.sin(rad)
    a, b = -dy, dx
    norm = math.hypot(a, b) or 1.0
    a, b = a / norm, b / norm
    c = a * pt[0] + b * pt[1]
    return (a, b, c)


def _parallel_line_through(base: LineABC, pt: Point) -> LineABC:
    a, b, _ = base
    c = a * pt[0] + b * pt[1]
    return (a, b, c)


def _intersect_abc(l1: LineABC, l2: LineABC) -> Optional[Point]:
    a1, b1, c1 = l1
    a2, b2, c2 = l2
    denom = a1 * b2 - b1 * a2
    if abs(denom) < 1e-9:
        return None
    x = (c1 * b2 - b1 * c2) / denom
    y = (a1 * c2 - c1 * a2) / denom
    return (x, y)


def _point_on_segment(seg: LineSegment) -> Point:
    return ((seg[0][0] + seg[1][0]) / 2.0, (seg[0][1] + seg[1][1]) / 2.0)


def _shift_line_to_segment(line: LineABC, seg: LineSegment) -> LineABC:
    a, b, _ = line
    mid = _point_on_segment(seg)
    c = a * mid[0] + b * mid[1]
    return (a, b, c)


def _lerp(a: Point, b: Point, t: float) -> Point:
    return (a[0] + (b[0] - a[0]) * t, a[1] + (b[1] - a[1]) * t)


def _horizontal_distance(angle_deg: float) -> float:
    return min(abs(angle_deg), abs(angle_deg - 180.0))


def _vertical_distance(angle_deg: float) -> float:
    return abs(angle_deg - 90.0)


def _diagonal_distance(angle_deg: float) -> float:
    return min(abs(angle_deg - 35.0), abs(angle_deg - 145.0))


def _detect_angles(lines: List[LineSegment]) -> tuple[float, float]:
    merged = _merge_lines_by_angle(lines, angle_tol=12.0)
    peaks = _dominant_angles(merged)
    if not peaks:
        return (0.0, 35.0)

    horiz = [a for a in peaks if _horizontal_distance(a) <= 15.0]
    theta_top = min(horiz, key=_horizontal_distance) if horiz else 0.0

    side_pool = [a for a in peaks if _horizontal_distance(a) >= 12.0]
    if side_pool:
        theta_side = min(side_pool, key=_diagonal_distance)
    else:
        theta_side = 35.0

    if min(abs(theta_top - theta_side), abs(abs(theta_top - theta_side) - 180.0)) < 12.0:
        theta_top = 0.0
        if _horizontal_distance(theta_side) <= 15.0:
            theta_side = 35.0
    return (theta_top, theta_side)


def _anchor_line_from_segment(seg: LineSegment, anchor: Point, target_angle: float) -> LineABC:
    ang = _line_angle(seg[0], seg[1])
    if min(abs(ang - target_angle), abs(ang - target_angle - 180.0)) <= 20.0:
        return _line_from_angle_point(_point_on_segment(seg), ang)
    return _line_from_angle_point(anchor, target_angle)


def _roi_anchor_points(roi: ROIBox) -> tuple[Point, Point, Point, Point]:
    x, y, w, h = roi.x, roi.y, roi.w, roi.h
    ix = w * config.HEX_INSET_X_FRAC
    iy = h * config.HEX_INSET_Y_FRAC
    top_mid = (x + w * 0.5, y + iy)
    bot_mid = (x + w * 0.5, y + h - iy)
    left_mid = (x + ix, y + h * 0.5)
    right_mid = (x + w - ix, y + h * 0.5)
    return top_mid, bot_mid, left_mid, right_mid


def build_standard_hex_formula(
    roi: ROIBox,
    lines: Optional[List[LineSegment]] = None,
    *,
    split_frac: float | None = None,
) -> Optional[HexFormula]:
    """
    Standard isometric trapezoid hex from 4 parallel line pairs + split fraction.

    Topology (3-block cluster, top view isometric):

        A -------- B -------- C     L_top
         \\         |         /
          \\        |        /
           F ------- E ------ D     L_bot

    Construction:
      1. L_top  angle θ_top through top ROI anchor
      2. L_bot  parallel L_top through bottom anchor
      3. L_left angle θ_side through left anchor
      4. L_right parallel L_left through right anchor
      5. A = L_top ∩ L_left,  C = L_top ∩ L_right
         F = L_bot ∩ L_left,  D = L_bot ∩ L_right
      6. B = lerp(A, C, t),  E = lerp(F, D, t)   with t = split_frac

    Guarantees: A,B,C collinear; F,E,D collinear; top ∥ bottom; left ∥ right;
    front face A-B-E-F and right face B-C-D-E are proper trapezoids.
    """
    lines = lines or []
    merged = _merge_lines_by_angle(lines, angle_tol=12.0)
    theta_top, theta_side = _detect_angles(lines)
    t = config.HEX_SPLIT_FRAC if split_frac is None else split_frac

    top_mid, bot_mid, left_mid, right_mid = _roi_anchor_points(roi)

    l_top = _line_from_angle_point(top_mid, theta_top)
    l_bot = _line_from_angle_point(bot_mid, theta_top)
    l_left = _line_from_angle_point(left_mid, theta_side)
    l_right = _line_from_angle_point(right_mid, theta_side)

    top_seg = _pick_line_near_angle(merged, theta_top, 15)
    side_seg = _pick_line_near_angle(merged, theta_side, 20)
    if top_seg:
        l_top = _anchor_line_from_segment(top_seg, top_mid, theta_top)
        l_bot = _parallel_line_through(l_top, bot_mid)
    if side_seg:
        l_left = _anchor_line_from_segment(side_seg, left_mid, theta_side)
        l_right = _parallel_line_through(l_left, right_mid)

    a = _intersect_abc(l_top, l_left)
    c = _intersect_abc(l_top, l_right)
    f = _intersect_abc(l_bot, l_left)
    d = _intersect_abc(l_bot, l_right)
    if None in (a, c, f, d):
        return None

    # Ensure left→right ordering on both rows (swap side lines if ROI tilt flipped them).
    if a[0] > c[0]:
        l_left, l_right = l_right, l_left
        a, c = c, a
        f, d = d, f

    b = _lerp(a, c, t)
    e = _lerp(f, d, t)

    vertices = {
        "A": Point2D(*a),
        "B": Point2D(*b),
        "C": Point2D(*c),
        "D": Point2D(*d),
        "E": Point2D(*e),
        "F": Point2D(*f),
    }
    return HexFormula(
        theta_top_deg=theta_top,
        theta_side_deg=theta_side,
        split_frac=t,
        top_line=l_top,
        bottom_line=l_bot,
        left_line=l_left,
        right_line=l_right,
        vertices=vertices,
    )


def export_hex_formula(
    roi: ROIBox,
    lines: Optional[List[LineSegment]] = None,
    *,
    split_frac: float | None = None,
) -> Optional[dict]:
    """Export JSON-serializable formula + vertex coordinates."""
    formula = build_standard_hex_formula(roi, lines, split_frac=split_frac)
    if formula is None:
        return None
    return formula.as_dict()


def compute_standard_hexagon(
    roi: ROIBox,
    lines: Optional[List[LineSegment]] = None,
    *,
    split_frac: float | None = None,
) -> Optional[Dict[str, Point2D]]:
    formula = build_standard_hex_formula(roi, lines, split_frac=split_frac)
    if formula is None:
        return None
    return dict(formula.vertices)

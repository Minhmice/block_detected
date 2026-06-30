from __future__ import annotations

from typing import Dict, List, Optional, Tuple

import numpy as np

from .edges import LineSegment
from .hex_formula import (
    HexFormula,
    build_standard_hex_formula,
    compute_standard_hexagon,
    export_hex_formula,
)
from .models import Point2D
from .roi import ROIBox
from .score import score_candidate, validate_topology

LABELS = "ABCDEF"


def _vertices_from_lines(
    l_top: tuple[float, float, float],
    l_bot: tuple[float, float, float],
    l_left: tuple[float, float, float],
    l_right: tuple[float, float, float],
    split_frac: float,
) -> Optional[Dict[str, Point2D]]:
    from .hex_formula import _intersect_abc, _lerp

    a = _intersect_abc(l_top, l_left)
    c = _intersect_abc(l_top, l_right)
    f = _intersect_abc(l_bot, l_left)
    d = _intersect_abc(l_bot, l_right)
    if None in (a, c, f, d):
        return None
    if a[0] > c[0]:
        a, c = c, a
        f, d = d, f
    b = _lerp(a, c, split_frac)
    e = _lerp(f, d, split_frac)
    return {k: Point2D(*p) for k, p in zip(LABELS, (a, b, c, d, e, f))}


def _offset_line(line: tuple[float, float, float], delta: float) -> tuple[float, float, float]:
    a, b, c = line
    return (a, b, c + delta)


def _tune_line_offsets(
    formula: HexFormula,
    edges: np.ndarray,
    roi: ROIBox,
) -> Dict[str, Point2D]:
    best_pts = dict(formula.vertices)
    best_score = score_candidate(best_pts, edges, roi, strict_topology=True)

    for d_top in range(-54, 55, 4):
        for d_side in range(-54, 55, 4):
            l_top = _offset_line(formula.top_line, float(d_top))
            l_bot = _offset_line(formula.bottom_line, float(d_top))
            l_left = _offset_line(formula.left_line, float(d_side))
            l_right = _offset_line(formula.right_line, float(d_side))
            pts = _vertices_from_lines(
                l_top, l_bot, l_left, l_right, formula.split_frac
            )
            if pts is None or not validate_topology(pts, strict=False):
                continue
            score = score_candidate(pts, edges, roi, strict_topology=True)
            if score > best_score:
                best_score = score
                best_pts = pts
    return best_pts


def fit_hexagon_from_lines(
    lines: List[LineSegment],
    roi: ROIBox,
    frame_shape: Tuple[int, int],
    edges: np.ndarray | None = None,
) -> Optional[Dict[str, Point2D]]:
    """Fit A–F: standard trapezoid formula, then optional line-offset edge tuning."""
    del frame_shape

    formula = build_standard_hex_formula(roi, lines)
    if formula is None:
        return None

    points = dict(formula.vertices)
    if edges is not None and edges.size:
        points = _tune_line_offsets(formula, edges, roi)

    if not validate_topology(points, strict=False):
        return None
    return points


def get_hex_formula_export(
    lines: List[LineSegment],
    roi: ROIBox,
) -> Optional[dict]:
    """Return formula parameters + vertices for debugging or external use."""
    return export_hex_formula(roi, lines)

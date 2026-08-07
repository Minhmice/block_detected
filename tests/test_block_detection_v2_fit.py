from __future__ import annotations

import math
from pathlib import Path

import cv2

from block_detection_v2.edges import detect_edges
from block_detection_v2.fit import fit_hexagon_from_lines, get_hex_formula_export
from block_detection_v2.hex_formula import build_standard_hex_formula
from block_detection_v2.preprocessing import preprocess
from block_detection_v2.roi import extract_cluster_roi
from block_detection_v2.score import validate_topology

_DATASET = Path(__file__).resolve().parents[1] / "block_dataset"


def _collinearity_error(p1, p2, p3) -> float:
    """Perpendicular distance of p2 from line p1-p3, normalized by |p1-p3|."""
    x1, y1 = p1.x, p1.y
    x2, y2 = p2.x, p2.y
    x3, y3 = p3.x, p3.y
    denom = math.hypot(x3 - x1, y3 - y1)
    if denom < 1e-6:
        return 0.0
    return abs((x2 - x1) * (y3 - y1) - (y2 - y1) * (x3 - x1)) / denom


def _pipeline(name: str):
    frame = cv2.imread(str(_DATASET / name))
    assert frame is not None
    color, gray = preprocess(frame)
    edges, lines = detect_edges(gray)
    roi = extract_cluster_roi(edges, color.shape[:2])
    assert roi is not None
    masked = cv2.bitwise_and(edges, roi.mask)
    filtered = [
        seg
        for seg in lines
        if roi.mask[int((seg[0][1] + seg[1][1]) / 2), int((seg[0][0] + seg[1][0]) / 2)]
    ]
    points = fit_hexagon_from_lines(filtered or lines, roi, color.shape[:2], edges=masked)
    return points, roi, filtered or lines


def test_fit_hexagon_dt50():
    points, _, _ = _pipeline("dt50.jpg")
    assert points is not None
    assert set(points.keys()) == set("ABCDEF")


def test_fit_topology_ordering():
    points, _, _ = _pipeline("dt50.jpg")
    assert points is not None
    assert validate_topology(points, strict=False)


def test_top_bottom_rows_collinear():
    points, roi, lines = _pipeline("dt50.jpg")
    assert points is not None
    a, b, c = points["A"], points["B"], points["C"]
    f, e, d = points["F"], points["E"], points["D"]
    assert _collinearity_error(a, b, c) < 1.0
    assert _collinearity_error(f, e, d) < 1.0

    formula = build_standard_hex_formula(roi, lines)
    assert formula is not None
    assert formula.split_frac == formula.as_dict()["split_frac"]


def test_export_hex_formula():
    points, roi, lines = _pipeline("dt50.jpg")
    assert points is not None
    exported = get_hex_formula_export(lines, roi)
    assert exported is not None
    assert "theta_top_deg" in exported
    assert "vertices" in exported
    assert set(exported["vertices"]) == set("ABCDEF")


def test_fit_returns_none_on_empty_roi():
    import numpy as np
    from block_detection_v2.roi import ROIBox

    empty = np.zeros((100, 100), dtype=np.uint8)
    roi = ROIBox(0, 0, 100, 100, empty, 0, block_mode=3)
    points = fit_hexagon_from_lines([], roi, (100, 100), edges=empty)
    assert points is None or validate_topology(points, strict=False)

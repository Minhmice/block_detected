"""Geometric intersections, validation, and candidate scoring."""

from __future__ import annotations

import math
from typing import Sequence

import numpy as np

from .config import HexDetectorConfig
from .models import BBox, HexPoints, LineSegment, ScoreBreakdown


def line_intersection(l1: LineSegment, l2: LineSegment) -> tuple[float, float] | None:
    x1, y1, x2, y2 = l1.x1, l1.y1, l1.x2, l1.y2
    x3, y3, x4, y4 = l2.x1, l2.y1, l2.x2, l2.y2
    denom = (x1 - x2) * (y3 - y4) - (y1 - y2) * (x3 - x4)
    if abs(denom) < 1e-9:
        return None
    px = ((x1 * y2 - y1 * x2) * (x3 - x4) - (x1 - x2) * (x3 * y4 - y3 * x4)) / denom
    py = ((x1 * y2 - y1 * x2) * (y3 - y4) - (y1 - y2) * (x3 * y4 - y3 * x4)) / denom
    return float(px), float(py)


def _segment_angle(p1: tuple[float, float], p2: tuple[float, float]) -> float:
    ang = math.degrees(math.atan2(p2[1] - p1[1], p2[0] - p1[0]))
    if ang < 0:
        ang += 180.0
    return ang


def _parallel_score_deg(a1: float, a2: float, tol: float) -> float:
    d = abs(a1 - a2) % 180.0
    d = min(d, 180.0 - d)
    if d <= tol:
        return 1.0
    return max(0.0, 1.0 - (d - tol) / max(tol, 1e-6))


def is_convex_polygon(points: Sequence[tuple[float, float]]) -> bool:
    if len(points) < 3:
        return False
    sign = 0
    n = len(points)
    for i in range(n):
        x1, y1 = points[i]
        x2, y2 = points[(i + 1) % n]
        x3, y3 = points[(i + 2) % n]
        cross = (x2 - x1) * (y3 - y2) - (y2 - y1) * (x3 - x2)
        if abs(cross) < 1e-6:
            continue
        s = 1 if cross > 0 else -1
        if sign == 0:
            sign = s
        elif s != sign:
            return False
    return sign != 0


def polygon_area(points: Sequence[tuple[float, float]]) -> float:
    if len(points) < 3:
        return 0.0
    area = 0.0
    n = len(points)
    for i in range(n):
        x1, y1 = points[i]
        x2, y2 = points[(i + 1) % n]
        area += x1 * y2 - x2 * y1
    return abs(area) / 2.0


# ---------------------------------------------------------------------------
# Relational outer-boundary / seam analysis
# ---------------------------------------------------------------------------


def _vertical_mid_x(ln: LineSegment) -> float:
    return (ln.x1 + ln.x2) / 2.0


def vertical_silhouette(vertical_lines: Sequence[LineSegment]) -> tuple[float, float] | None:
    """Return (x_left, x_right) — the horizontal extent spanned by verticals."""
    if not vertical_lines:
        return None
    xs = [_vertical_mid_x(ln) for ln in vertical_lines]
    return min(xs), max(xs)


def interior_vertical_xs(
    vertical_lines: Sequence[LineSegment],
    tol: float,
) -> list[float]:
    """Midpoint-x of verticals that are neither leftmost nor rightmost.

    Such lines are candidate INTERNAL SEAMS between blocks (they sit inside the
    cluster silhouette rather than on its outer boundary).
    """
    sil = vertical_silhouette(vertical_lines)
    if sil is None:
        return []
    x_left, x_right = sil
    span = max(x_right - x_left, 1.0)
    out: list[float] = []
    for ln in vertical_lines:
        mx = _vertical_mid_x(ln)
        if (mx - x_left) > tol * span and (x_right - mx) > tol * span:
            out.append(mx)
    return out


def outer_boundary_quality(
    pts: dict[str, tuple[float, float] | None],
    mode: str,
    vertical_lines: Sequence[LineSegment],
    cfg: HexDetectorConfig,
) -> tuple[float, bool, dict[str, float]]:
    """Relational score: does this candidate hug the cluster's outer silhouette?

    Returns (quality[0..1], is_seam, detail). No absolute ROI positions used —
    only the candidate's edges relative to the full set of vertical lines.

    - AF (left vertical of front) should sit at the LEFT silhouette extent.
    - The outer-right vertical (CD for hex, BE for rectangle) should sit at the
      RIGHT silhouette extent.
    - If a vertical exists beyond either boundary, that edge is an internal
      seam (or the candidate misses part of the cluster) -> is_seam=True.
    """
    a, b, e, f = pts.get("A"), pts.get("B"), pts.get("E"), pts.get("F")
    c, d = pts.get("C"), pts.get("D")
    if None in (a, b, e, f):
        return 0.0, False, {}
    assert a and b and e and f
    sil = vertical_silhouette(vertical_lines)
    if sil is None:
        return 0.5, False, {"reason": 0.0}
    x_left, x_right = sil
    width = max(x_right - x_left, 1.0)

    af_x = (a[0] + f[0]) / 2.0
    if mode == "hex" and c is not None and d is not None:
        right_x = (c[0] + d[0]) / 2.0
    else:
        right_x = (b[0] + e[0]) / 2.0

    left_gap = max(0.0, af_x - x_left) / width      # verticals to the left of AF
    right_gap = max(0.0, x_right - right_x) / width  # verticals to the right of outer edge

    left_score = max(0.0, 1.0 - min(left_gap, 1.0))
    right_score = max(0.0, 1.0 - min(right_gap, 1.0))
    quality = 0.5 * left_score + 0.5 * right_score

    tol = cfg.outer_boundary_tol_ratio
    is_seam = left_gap > tol or right_gap > tol
    detail = {
        "left_gap": round(left_gap, 3),
        "right_gap": round(right_gap, 3),
        "quality": round(quality, 3),
    }
    return quality, is_seam, detail


def _area_boundary_composite(
    pts: dict[str, tuple[float, float] | None],
    mode: str,
    roi_w: int,
    roi_h: int,
    vertical_lines: Sequence[LineSegment] | None,
    cfg: HexDetectorConfig,
    area_score: float,
) -> tuple[float, bool, dict[str, float]]:
    """Blend front area with relational outer-boundary quality + seam penalty.

    Returns (composite[0..1], is_seam, detail).
    """
    if not vertical_lines:
        return area_score, False, {}
    quality, is_seam, detail = outer_boundary_quality(pts, mode, vertical_lines, cfg)
    composite = 0.4 * area_score + 0.6 * quality
    if is_seam:
        composite *= max(0.0, 1.0 - cfg.seam_penalty_weight)
    return float(np.clip(composite, 0.0, 1.0)), is_seam, detail


# ---------------------------------------------------------------------------
# Front-face (4-point) detection
# ---------------------------------------------------------------------------


def points_from_front_lines(
    af: LineSegment,
    be: LineSegment,
    ab: LineSegment,
    fe: LineSegment,
) -> dict[str, tuple[float, float] | None] | None:
    """Compute the four front-face intersection points.

    Returns dict with A, B, E, F (plus C/D None) or None if any intersection fails.
    """
    a = line_intersection(af, ab)
    b = line_intersection(be, ab)
    f = line_intersection(af, fe)
    e = line_intersection(be, fe)
    if None in (a, b, f, e):
        return None
    return {
        "A": a,
        "B": b,
        "C": None,
        "D": None,
        "E": e,
        "F": f,
    }


def validate_front_points(
    pts: dict[str, tuple[float, float] | None],
    roi_w: int,
    roi_h: int,
    cfg: HexDetectorConfig,
) -> tuple[bool, str]:
    """Validate a 4-point A-B-E-F front quadrilateral.

    Checks that all four points are present, within ROI bounds,
    form a convex quadrilateral with reasonable area, and
    have parallel vertical and horizontal edges.
    Also checks BE position and front width constraints.
    """
    a, b, e, f = pts.get("A"), pts.get("B"), pts.get("E"), pts.get("F")
    if None in (a, b, e, f):
        return False, "missing_point"

    assert a and b and e and f

    m = cfg.point_inside_margin_px
    for name, p in [("A", a), ("B", b), ("E", e), ("F", f)]:
        if p[0] < -m or p[1] < -m or p[0] > roi_w + m or p[1] > roi_h + m:
            return False, f"{name}_outside_roi"

    # x ordering on front face
    if not (a[0] < b[0]):
        return False, "x_order_top"
    if not (f[0] < e[0]):
        return False, "x_order_bottom"

    # top should be above bottom
    top_y = (a[1] + b[1]) / 2.0
    bot_y = (f[1] + e[1]) / 2.0
    if top_y >= bot_y:
        return False, "top_below_bottom"

    poly = [a, b, e, f]
    if not is_convex_polygon(poly):
        return False, "not_convex"

    # vertical edges should be parallel
    af_ang = _segment_angle(a, f)
    be_ang = _segment_angle(b, e)
    if _parallel_score_deg(af_ang, be_ang, cfg.parallel_tol_deg) < 0.3:
        return False, "vertical_not_parallel"

    # front horizontal edges should be parallel
    ab_ang = _segment_angle(a, b)
    fe_ang = _segment_angle(f, e)
    if _parallel_score_deg(ab_ang, fe_ang, cfg.parallel_tol_deg) < 0.3:
        return False, "front_not_parallel"

    front_area = polygon_area(poly)
    roi_area = float(roi_w * roi_h)
    if roi_area <= 0 or front_area / roi_area < cfg.min_front_area_ratio:
        return False, "front_area_small"

    # NOTE: absolute-position constraints (front_too_narrow / be_too_left /
    # be_too_right) intentionally removed. Whether BE is a real shared edge vs
    # an internal seam is decided relationally by outer-boundary scoring, not
    # by absolute x-position inside the (padded, off-center) ROI.
    return True, ""


# ---------------------------------------------------------------------------
# Full hex (6-point) validation
# ---------------------------------------------------------------------------


def points_from_lines(
    af: LineSegment,
    be: LineSegment,
    cd: LineSegment,
    ab: LineSegment,
    fe: LineSegment,
    bc: LineSegment,
    ed: LineSegment,
) -> HexPoints | None:
    a = line_intersection(af, ab)
    b = line_intersection(be, ab)
    f = line_intersection(af, fe)
    e = line_intersection(be, fe)
    c = line_intersection(cd, bc)
    d = line_intersection(cd, ed)
    if None in (a, b, f, e, c, d):
        return None
    return HexPoints(A=a, B=b, C=c, D=d, E=e, F=f)


def roi_to_frame_point(pt: tuple[float, float], roi_bbox: BBox) -> tuple[float, float]:
    return pt[0] + roi_bbox.x1, pt[1] + roi_bbox.y1


def frame_points_conflict(
    last_points: dict[str, tuple[float, float] | None],
    candidate: HexPoints,
    norm_w: float,
    norm_h: float,
    threshold: float,
) -> bool:
    """True when mean normalized point distance exceeds conflict threshold."""
    dists: list[float] = []
    scale = max(math.hypot(norm_w, norm_h), 1.0)
    cand = candidate.as_dict()
    for key in ("A", "B", "C", "D", "E", "F"):
        p = last_points.get(key)
        q = cand.get(key)
        if p is None or q is None:
            continue
        dists.append(math.hypot(p[0] - q[0], p[1] - q[1]) / scale)
    if not dists:
        return False
    return float(np.mean(dists)) > threshold


def validate_hex_points(
    pts: HexPoints,
    roi_w: int,
    roi_h: int,
    cfg: HexDetectorConfig,
) -> tuple[bool, str]:
    if None in (pts.A, pts.B, pts.C, pts.D, pts.E, pts.F):
        return False, "missing_point"

    m = cfg.point_inside_margin_px
    for name, p in pts.as_dict().items():
        if p is None:
            continue
        if p[0] < -m or p[1] < -m or p[0] > roi_w + m or p[1] > roi_h + m:
            return False, f"{name}_outside_roi"

    a, b, c, d, e, f = pts.A, pts.B, pts.C, pts.D, pts.E, pts.F
    assert a and b and c and d and e and f

    if not (a[0] < b[0] < c[0]):
        return False, "x_order_top"
    if not (f[0] < e[0] < d[0]):
        return False, "x_order_bottom"

    top_y = (a[1] + b[1] + c[1]) / 3.0
    bot_y = (f[1] + e[1] + d[1]) / 3.0
    if top_y >= bot_y:
        return False, "top_below_bottom"

    poly = [a, b, c, d, e, f]
    if not is_convex_polygon(poly):
        return False, "not_convex"

    af_ang = _segment_angle(a, f)
    be_ang = _segment_angle(b, e)
    cd_ang = _segment_angle(c, d)
    if min(_parallel_score_deg(af_ang, be_ang, cfg.parallel_tol_deg),
           _parallel_score_deg(be_ang, cd_ang, cfg.parallel_tol_deg)) < 0.3:
        return False, "vertical_not_parallel"

    ab_ang = _segment_angle(a, b)
    fe_ang = _segment_angle(f, e)
    if _parallel_score_deg(ab_ang, fe_ang, cfg.parallel_tol_deg) < 0.3:
        return False, "front_not_parallel"

    bc_ang = _segment_angle(b, c)
    ed_ang = _segment_angle(e, d)
    if _parallel_score_deg(bc_ang, ed_ang, cfg.parallel_tol_deg) < 0.3:
        return False, "right_not_parallel"

    front_area = polygon_area([a, b, e, f])
    roi_area = float(roi_w * roi_h)
    if roi_area <= 0 or front_area / roi_area < cfg.min_front_area_ratio:
        return False, "front_area_small"

    right_width = c[0] - b[0]
    if right_width < 0:
        return False, "right_inverted"

    if right_width / max(roi_w, 1) < cfg.min_right_width_ratio:
        return False, "right_too_narrow"

    # --- right/front width ratio constraint ---
    front_width = b[0] - a[0]
    if front_width > 0:
        rf_ratio = right_width / front_width
        if rf_ratio < cfg.min_right_front_ratio or rf_ratio > cfg.max_right_front_ratio:
            return False, "right_front_ratio_out_of_range"

    return True, ""


def should_use_rectangle_mode(pts: HexPoints, roi_w: int, cfg: HexDetectorConfig) -> bool:
    if pts.B is None or pts.C is None:
        return True
    width = pts.C[0] - pts.B[0]
    return width / max(roi_w, 1) < cfg.rectangle_mode_right_width_ratio


# ---------------------------------------------------------------------------
# Component scoring
# ---------------------------------------------------------------------------


def _edge_fraction(
    segments: Sequence[tuple[tuple[float, float] | None, tuple[float, float] | None]],
    edges: np.ndarray,
) -> float:
    """Vectorized fraction of in-bounds samples (over all segments) on an edge pixel."""
    if edges.size == 0:
        return 0.0
    h, w = edges.shape[:2]
    xs_all: list[np.ndarray] = []
    ys_all: list[np.ndarray] = []
    for p1, p2 in segments:
        if p1 is None or p2 is None:
            continue
        steps = max(int(np.hypot(p2[0] - p1[0], p2[1] - p1[1])), 1)
        t = np.linspace(0.0, 1.0, steps)
        xs_all.append((p1[0] + t * (p2[0] - p1[0])).astype(np.int32))
        ys_all.append((p1[1] + t * (p2[1] - p1[1])).astype(np.int32))
    if not xs_all:
        return 0.0
    xs = np.concatenate(xs_all)
    ys = np.concatenate(ys_all)
    valid = (xs >= 0) & (xs < w) & (ys >= 0) & (ys < h)
    if not valid.any():
        return 0.0
    return float((edges[ys[valid], xs[valid]] > 0).mean())


def _edge_support_for_points(
    pts: dict[str, tuple[float, float] | None],
    edges: np.ndarray,
) -> float:
    """Edge support along the active segments of a point set."""
    a, b, c, d, e, f = (
        pts.get("A"), pts.get("B"), pts.get("C"),
        pts.get("D"), pts.get("E"), pts.get("F"),
    )
    segments = [(a, b), (b, e), (e, f), (f, a), (b, e)]
    if c is not None and d is not None:
        segments.extend([(b, c), (c, d), (d, e)])
    return _edge_fraction(segments, edges)


def edge_support_score(pts: HexPoints, edges: np.ndarray) -> float:
    """Edge support along the full hex perimeter + shared edge."""
    segments = [
        (pts.A, pts.B), (pts.B, pts.C), (pts.C, pts.D),
        (pts.D, pts.E), (pts.E, pts.F), (pts.F, pts.A), (pts.B, pts.E),
    ]
    return _edge_fraction(segments, edges)


def parallelism_score(pts: HexPoints, cfg: HexDetectorConfig) -> float:
    if None in (pts.A, pts.B, pts.C, pts.D, pts.E, pts.F):
        return 0.0
    assert pts.A and pts.B and pts.C and pts.D and pts.E and pts.F
    v1 = _parallel_score_deg(_segment_angle(pts.A, pts.F), _segment_angle(pts.B, pts.E), cfg.parallel_tol_deg)
    v2 = _parallel_score_deg(_segment_angle(pts.B, pts.E), _segment_angle(pts.C, pts.D), cfg.parallel_tol_deg)
    h1 = _parallel_score_deg(_segment_angle(pts.A, pts.B), _segment_angle(pts.F, pts.E), cfg.parallel_tol_deg)
    r1 = _parallel_score_deg(_segment_angle(pts.B, pts.C), _segment_angle(pts.E, pts.D), cfg.parallel_tol_deg)
    return float(np.mean([v1, v2, h1, r1]))


def _front_parallelism_score(
    pts: dict[str, tuple[float, float] | None],
    cfg: HexDetectorConfig,
) -> float:
    """Parallelism for front-face only (A, B, E, F)."""
    a, b, e, f = pts.get("A"), pts.get("B"), pts.get("E"), pts.get("F")
    if None in (a, b, e, f):
        return 0.0
    assert a and b and e and f
    v1 = _parallel_score_deg(_segment_angle(a, f), _segment_angle(b, e), cfg.parallel_tol_deg)
    h1 = _parallel_score_deg(_segment_angle(a, b), _segment_angle(f, e), cfg.parallel_tol_deg)
    return float(np.mean([v1, h1]))


def topology_score(pts: HexPoints, roi_w: int, roi_h: int, cfg: HexDetectorConfig) -> float:
    """Validate topology using the active config (not a fresh one)."""
    ok, _ = validate_hex_points(pts, roi_w, roi_h, cfg)
    return 1.0 if ok else 0.0


def _front_topology_score(
    pts: dict[str, tuple[float, float] | None],
    roi_w: int,
    roi_h: int,
    cfg: HexDetectorConfig,
) -> float:
    ok, _ = validate_front_points(pts, roi_w, roi_h, cfg)
    return 1.0 if ok else 0.0


def area_position_score(pts: HexPoints, roi_w: int, roi_h: int, cfg: HexDetectorConfig) -> float:
    if None in (pts.A, pts.B, pts.E, pts.F):
        return 0.0
    assert pts.A and pts.B and pts.E and pts.F
    front = polygon_area([pts.A, pts.B, pts.E, pts.F])
    roi_area = float(roi_w * roi_h)
    if roi_area <= 0:
        return 0.0
    ratio = front / roi_area
    target = cfg.min_front_area_ratio * 2.0
    return float(np.clip(ratio / max(target, 1e-6), 0.0, 1.0))


def _front_area_position_score(
    pts: dict[str, tuple[float, float] | None],
    roi_w: int,
    roi_h: int,
    cfg: HexDetectorConfig,
) -> float:
    a, b, e, f = pts.get("A"), pts.get("B"), pts.get("E"), pts.get("F")
    if None in (a, b, e, f):
        return 0.0
    assert a and b and e and f
    front = polygon_area([a, b, e, f])
    roi_area = float(roi_w * roi_h)
    if roi_area <= 0:
        return 0.0
    ratio = front / roi_area
    target = cfg.min_front_area_ratio * 2.0
    return float(np.clip(ratio / max(target, 1e-6), 0.0, 1.0))


def temporal_similarity_score(
    pts: HexPoints,
    prev: HexPoints | None,
    roi_w: int,
    roi_h: int,
) -> float:
    if prev is None:
        return 0.5
    dists: list[float] = []
    for key in ("A", "B", "C", "D", "E", "F"):
        p = getattr(pts, key)
        q = getattr(prev, key)
        if p is None or q is None:
            continue
        d = math.hypot(p[0] - q[0], p[1] - q[1])
        norm = math.hypot(roi_w, roi_h)
        dists.append(d / max(norm, 1.0))
    if not dists:
        return 0.5
    mean_d = float(np.mean(dists))
    return float(np.clip(1.0 - mean_d * 5.0, 0.0, 1.0))


# ---------------------------------------------------------------------------
# Composite scoring
# ---------------------------------------------------------------------------


def score_front_candidate(
    frame_pts: dict[str, tuple[float, float] | None],
    roi_pts: dict[str, tuple[float, float] | None],
    edges: np.ndarray,
    roi_w: int,
    roi_h: int,
    cfg: HexDetectorConfig,
    prev_pts: HexPoints | None = None,
    vertical_lines: Sequence[LineSegment] | None = None,
) -> ScoreBreakdown:
    """Score a front-face (4-point) candidate, returning a full breakdown.

    Args:
        frame_pts: points in frame coordinates (for temporal score)
        roi_pts: points in ROI-local coordinates (for geometry)
        edges: edge image
        roi_w, roi_h: ROI dimensions
        cfg: active config
        prev_pts: previous result for temporal smoothing
        vertical_lines: merged vertical lines (for relational outer-boundary)
    """
    edge = _edge_support_for_points(roi_pts, edges)
    parallel = _front_parallelism_score(roi_pts, cfg)
    topo = _front_topology_score(roi_pts, roi_w, roi_h, cfg)
    area_raw = _front_area_position_score(roi_pts, roi_w, roi_h, cfg)
    area, _seam, _detail = _area_boundary_composite(
        roi_pts, "rectangle", roi_w, roi_h, vertical_lines, cfg, area_raw,
    )

    # Temporal: need prev in frame coordinates
    temporal = 0.5
    if prev_pts is not None:
        temporal = temporal_similarity_score_from_dict(frame_pts, prev_pts, roi_w, roi_h)

    total = (
        cfg.weight_edge_support * edge
        + cfg.weight_parallelism * parallel
        + cfg.weight_topology * topo
        + cfg.weight_area_position * area
        + cfg.weight_temporal * temporal
    )
    return ScoreBreakdown(
        edge_support=edge,
        parallelism=parallel,
        topology=topo,
        area_position=area,
        temporal=temporal,
        total=total,
    )


def score_hex_candidate(
    frame_pts: dict[str, tuple[float, float] | None],
    edges: np.ndarray,
    roi_w: int,
    roi_h: int,
    cfg: HexDetectorConfig,
    hex_pts: HexPoints,
    prev_pts: HexPoints | None = None,
    effective_bbox: BBox | None = None,
    vertical_lines: Sequence[LineSegment] | None = None,
) -> ScoreBreakdown:
    """Score a 6-point hex candidate, returning a full breakdown."""
    edge = edge_support_score(hex_pts, edges)
    parallel = parallelism_score(hex_pts, cfg)
    topo = topology_score(hex_pts, roi_w, roi_h, cfg)
    area_raw = area_position_score(hex_pts, roi_w, roi_h, cfg)
    area, _seam, _detail = _area_boundary_composite(
        hex_pts.as_dict(), "hex", roi_w, roi_h, vertical_lines, cfg, area_raw,
    )
    frame_hex = hex_pts
    if effective_bbox is not None:
        frame_hex = HexPoints(
            A=roi_to_frame_point(hex_pts.A, effective_bbox) if hex_pts.A else None,
            B=roi_to_frame_point(hex_pts.B, effective_bbox) if hex_pts.B else None,
            C=roi_to_frame_point(hex_pts.C, effective_bbox) if hex_pts.C else None,
            D=roi_to_frame_point(hex_pts.D, effective_bbox) if hex_pts.D else None,
            E=roi_to_frame_point(hex_pts.E, effective_bbox) if hex_pts.E else None,
            F=roi_to_frame_point(hex_pts.F, effective_bbox) if hex_pts.F else None,
        )
    temporal = temporal_similarity_score(frame_hex, prev_pts, roi_w, roi_h)

    total = (
        cfg.weight_edge_support * edge
        + cfg.weight_parallelism * parallel
        + cfg.weight_topology * topo
        + cfg.weight_area_position * area
        + cfg.weight_temporal * temporal
    )
    return ScoreBreakdown(
        edge_support=edge,
        parallelism=parallel,
        topology=topo,
        area_position=area,
        temporal=temporal,
        total=total,
    )


def temporal_similarity_score_from_dict(
    pts: dict[str, tuple[float, float] | None],
    prev: HexPoints | None,
    roi_w: int,
    roi_h: int,
) -> float:
    """Temporal similarity using a dict of points."""
    if prev is None:
        return 0.5
    dists: list[float] = []
    for key in ("A", "B", "C", "D", "E", "F"):
        p = pts.get(key)
        q = getattr(prev, key)
        if p is None or q is None:
            continue
        d = math.hypot(p[0] - q[0], p[1] - q[1])
        norm = math.hypot(roi_w, roi_h)
        dists.append(d / max(norm, 1.0))
    if not dists:
        return 0.5
    mean_d = float(np.mean(dists))
    return float(np.clip(1.0 - mean_d * 5.0, 0.0, 1.0))

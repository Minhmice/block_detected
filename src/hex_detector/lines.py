"""Line detection, filtering, grouping, and merging."""

from __future__ import annotations

import logging
import math

import cv2
import numpy as np

from .config import HexDetectorConfig
from .models import LineGroups, LineSegment

logger = logging.getLogger(__name__)


def detect_raw_lines(edges: np.ndarray, roi_w: int, roi_h: int, cfg: HexDetectorConfig) -> list[LineSegment]:
  if edges.size == 0 or roi_w <= 0 or roi_h <= 0:
    return []

  min_len = max(cfg.min_line_length_px, int(min(roi_w, roi_h) * cfg.hough_min_line_length_ratio))
  lines = cv2.HoughLinesP(
    edges,
    rho=cfg.hough_rho,
    theta=np.deg2rad(cfg.hough_theta_deg),
    threshold=cfg.hough_threshold,
    minLineLength=min_len,
    maxLineGap=cfg.hough_max_line_gap,
  )
  if lines is None:
    return []

  out: list[LineSegment] = []
  for seg in lines.reshape(-1, 4):
    out.append(LineSegment(float(seg[0]), float(seg[1]), float(seg[2]), float(seg[3])))
  return out


def _angle_distance_deg(a: float, b: float) -> float:
  d = abs(a - b) % 180.0
  return min(d, 180.0 - d)


def _line_edge_support(ln: LineSegment, edges: np.ndarray) -> float:
  """Fraction of sampled points along the segment that lie on an edge pixel.

  Vectorized + capped sampling (<=32 points) — cheap enough for the Pi.
  """
  if edges.size == 0:
    return 0.0
  h, w = edges.shape[:2]
  steps = int(min(max(ln.length(), 1.0), 32.0))
  t = np.linspace(0.0, 1.0, steps)
  xs = np.clip((ln.x1 + t * (ln.x2 - ln.x1)).astype(np.int32), 0, w - 1)
  ys = np.clip((ln.y1 + t * (ln.y2 - ln.y1)).astype(np.int32), 0, h - 1)
  return float((edges[ys, xs] > 0).mean())


def _line_dist_to_border(ln: LineSegment, roi_w: int, roi_h: int) -> float:
  """Min distance from the line midpoint to any ROI border, normalized by ROI size."""
  mx, my = ln.midpoint()
  d = min(mx, my, roi_w - mx, roi_h - my)
  norm = float(max(roi_w, roi_h, 1))
  return max(0.0, d) / norm


def enrich_lines(
  lines: list[LineSegment],
  edges: np.ndarray,
  roi_w: int,
  roi_h: int,
) -> list[LineSegment]:
  """Attach per-line edge_support and dist_to_border metadata."""
  out: list[LineSegment] = []
  for ln in lines:
    out.append(
      LineSegment(
        ln.x1, ln.y1, ln.x2, ln.y2,
        group=ln.group,
        edge_support=_line_edge_support(ln, edges),
        dist_to_border=_line_dist_to_border(ln, roi_w, roi_h),
      )
    )
  return out


def filter_lines(
  lines: list[LineSegment],
  roi_w: int,
  roi_h: int,
  cfg: HexDetectorConfig,
) -> list[LineSegment]:
  if not lines or roi_w <= 0 or roi_h <= 0:
    return []

  margin_x = roi_w * cfg.roi_edge_margin_ratio
  margin_y = roi_h * cfg.roi_edge_margin_ratio
  pallet_y = roi_h * cfg.pallet_line_bottom_ratio
  kept: list[LineSegment] = []

  for ln in lines:
    if ln.length() < cfg.min_line_length_px:
      continue

    mx, my = ln.midpoint()
    if mx < margin_x or mx > roi_w - margin_x or my < margin_y or my > roi_h - margin_y:
      continue

    ang = ln.angle_deg()
    if my > pallet_y and _angle_distance_deg(ang, 0.0) < cfg.pallet_line_angle_tol_deg:
      continue
    if my > pallet_y and _angle_distance_deg(ang, 180.0) < cfg.pallet_line_angle_tol_deg:
      continue

    kept.append(ln)
  return kept


def _group_targets(cfg: HexDetectorConfig) -> list[tuple[str, float, float]]:
  return [
    ("vertical", cfg.vertical_angle_center, cfg.vertical_angle_tol_deg),
    ("front_horizontal", cfg.front_horizontal_target_deg, cfg.front_horizontal_angle_tol_deg),
    ("right_diagonal", cfg.right_diagonal_target_deg, cfg.right_diagonal_angle_tol_deg),
  ]


def classify_line_group(
  angle: float,
  cfg: HexDetectorConfig,
) -> tuple[str | None, float]:
  """Assign line to exactly one group — smallest angular error within tolerance."""
  best_group: str | None = None
  best_err = float("inf")
  for name, target, tol in _group_targets(cfg):
    err = _angle_distance_deg(angle, target)
    if err <= tol and err < best_err:
      best_err = err
      best_group = name
  return best_group, best_err if best_group is not None else 0.0


def group_lines(
  lines: list[LineSegment],
  cfg: HexDetectorConfig,
) -> tuple[LineGroups, list[dict[str, float | str | None]]]:
  """Group each line into at most one bucket; log angle / group / angular error."""
  groups = LineGroups()
  classifications: list[dict[str, float | str | None]] = []

  for ln in lines:
    ang = ln.angle_deg()
    g, err = classify_line_group(ang, cfg)
    mx, my = ln.midpoint()
    rec: dict[str, float | str | None] = {
      # legacy keys (kept for existing tests / tooling)
      "selected_group": g,
      "angular_error_deg": round(err, 3) if g else None,
      # convenience keys (dataset debugger)
      "angle": round(ang, 1),
      "group": g or "none",
      "angular_err": round(err, 1) if err < float("inf") else 99.0,
      "length": round(ln.length(), 1),
      "mid_x": round(mx, 1),
      "mid_y": round(my, 1),
    }
    classifications.append(rec)
    if cfg.line_group_log_enabled and g is not None:
      logger.debug(
        "line group angle=%.2f group=%s err=%.2f",
        ang,
        g,
        err,
      )
    if g is None:
      continue
    tagged = LineSegment(ln.x1, ln.y1, ln.x2, ln.y2, group=g)
    if g == "vertical":
      groups.vertical.append(tagged)
    elif g == "front_horizontal":
      groups.front_horizontal.append(tagged)
    else:
      groups.right_diagonal.append(tagged)
  return groups, classifications


def _line_offset_metric(ln: LineSegment) -> float:
  """Perpendicular offset proxy for vertical-ish lines (x at mid), horizontal (y at mid)."""
  mx, my = ln.midpoint()
  ang = ln.angle_deg()
  if _angle_distance_deg(ang, 90.0) < 45.0:
    return mx
  return my


def merge_parallel_lines(lines: list[LineSegment], roi_size: float, cfg: HexDetectorConfig) -> list[LineSegment]:
  if not lines:
    return []

  dist_tol = roi_size * cfg.merge_distance_tol_ratio
  # Precompute (angle, offset) once per line — merge is O(n^2), so recomputing
  # angle_deg()/offset inside the loop dominated latency.
  annotated: list[tuple[LineSegment, float, float]] = [
    (ln, ln.angle_deg(), _line_offset_metric(ln)) for ln in lines
  ]
  annotated.sort(key=lambda t: (t[2], t[1]))

  clusters: list[list[LineSegment]] = []
  cluster_refs: list[tuple[float, float]] = []  # (angle, offset) of cluster head
  for ln, ang, off in annotated:
    placed = False
    for idx, (ref_ang, ref_off) in enumerate(cluster_refs):
      if (
        _angle_distance_deg(ang, ref_ang) <= cfg.merge_angle_tol_deg
        and abs(off - ref_off) <= dist_tol
      ):
        clusters[idx].append(ln)
        placed = True
        break
    if not placed:
      clusters.append([ln])
      cluster_refs.append((ang, off))

  merged: list[LineSegment] = []
  for cluster in clusters:
    xs = [c.x1 for c in cluster] + [c.x2 for c in cluster]
    ys = [c.y1 for c in cluster] + [c.y2 for c in cluster]
    ang = float(np.mean([c.angle_deg() for c in cluster]))
    rad = math.radians(ang)
    cx, cy = float(np.mean(xs)), float(np.mean(ys))
    half = float(np.mean([c.length() for c in cluster])) / 2.0
    dx, dy = math.cos(rad) * half, math.sin(rad) * half
    merged.append(
      LineSegment(
        cx - dx, cy - dy, cx + dx, cy + dy,
        group=cluster[0].group,
        edge_support=float(max((c.edge_support for c in cluster), default=0.0)),
        dist_to_border=float(np.mean([c.dist_to_border for c in cluster])),
      )
    )

  merged.sort(key=lambda l: _line_offset_metric(l))
  return merged[: cfg.max_lines_per_group]


def merge_line_groups(groups: LineGroups, roi_w: int, roi_h: int, cfg: HexDetectorConfig) -> LineGroups:
  size = float(max(roi_w, roi_h))
  return LineGroups(
    vertical=merge_parallel_lines(groups.vertical, size, cfg),
    front_horizontal=merge_parallel_lines(groups.front_horizontal, size, cfg),
    right_diagonal=merge_parallel_lines(groups.right_diagonal, size, cfg),
  )


def _vertical_sort_key(ln: LineSegment) -> float:
  return _line_offset_metric(ln)


def pick_front_line_combinations(
    groups: LineGroups,
    cfg: HexDetectorConfig,
) -> list[tuple[LineSegment, LineSegment, LineSegment, LineSegment]]:
  """Generate front-face tuples (AF, BE, AB, FE) with AF left of BE.

  All valid vertical pairs are emitted (bounded by max_front_candidates).
  """
  vertical = sorted(groups.vertical, key=_vertical_sort_key)
  fh = groups.front_horizontal
  if len(vertical) < 2 or len(fh) < 2:
    return []

  candidates: list[tuple[LineSegment, LineSegment, LineSegment, LineSegment]] = []
  n = len(vertical)
  for i in range(n):
    for j in range(n):
      if i == j:
        continue
      af = vertical[i]
      be = vertical[j]
      if _vertical_sort_key(af) >= _vertical_sort_key(be):
        continue
      for ab in fh:
        for fe in fh:
          if ab is fe:
            continue
          candidates.append((af, be, ab, fe))
          if len(candidates) >= cfg.max_front_candidates:
            return candidates
  return candidates


def pick_right_line_combinations(
    groups: LineGroups,
    cfg: HexDetectorConfig,
) -> list[tuple[LineSegment, LineSegment, LineSegment]]:
    """Generate right-face upgrade tuples: (CD, BC, ED) line proxies.

    Relational (no hard-coded rightmost): CD may be ANY vertical line. Which
    vertical is the true outer edge is decided later by validation (C.x > B.x)
    and outer-boundary scoring, not by absolute position here. Bounded by
    max_right_candidates.
    """
    vertical = sorted(groups.vertical, key=_vertical_sort_key)
    rd = groups.right_diagonal
    if len(vertical) < 1 or len(rd) < 2:
        return []

    candidates: list[tuple[LineSegment, LineSegment, LineSegment]] = []
    # Prefer verticals nearer the right extent first (more likely CD) but still
    # allow all — this only affects candidate ordering, not a hard filter.
    for cd in reversed(vertical):
        for bc in rd:
            for ed in rd:
                if bc is ed:
                    continue
                candidates.append((cd, bc, ed))
                if len(candidates) >= cfg.max_right_candidates:
                    return candidates
    return candidates

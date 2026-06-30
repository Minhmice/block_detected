"""Line detection, filtering, grouping, and merging."""

from __future__ import annotations

import math

import cv2
import numpy as np

from .config import HexDetectorConfig
from .models import BBox, LineGroups, LineSegment


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


def classify_line_group(angle: float, cfg: HexDetectorConfig) -> str | None:
  if _angle_distance_deg(angle, cfg.vertical_angle_center) <= cfg.vertical_angle_tol_deg:
    return "vertical"
  if _angle_distance_deg(angle, cfg.front_horizontal_target_deg) <= cfg.front_horizontal_angle_tol_deg:
    return "front_horizontal"
  if _angle_distance_deg(angle, cfg.right_diagonal_target_deg) <= cfg.right_diagonal_angle_tol_deg:
    return "right_diagonal"
  return None


def group_lines(lines: list[LineSegment], cfg: HexDetectorConfig) -> LineGroups:
  groups = LineGroups()
  for ln in lines:
    g = classify_line_group(ln.angle_deg(), cfg)
    if g is None:
      continue
    tagged = LineSegment(ln.x1, ln.y1, ln.x2, ln.y2, group=g)
    if g == "vertical":
      groups.vertical.append(tagged)
    elif g == "front_horizontal":
      groups.front_horizontal.append(tagged)
    else:
      groups.right_diagonal.append(tagged)
  return groups


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
  clusters: list[list[LineSegment]] = []

  for ln in sorted(lines, key=lambda l: (_line_offset_metric(l), l.angle_deg())):
    placed = False
    for cluster in clusters:
      ref = cluster[0]
      if (
        _angle_distance_deg(ln.angle_deg(), ref.angle_deg()) <= cfg.merge_angle_tol_deg
        and abs(_line_offset_metric(ln) - _line_offset_metric(ref)) <= dist_tol
      ):
        cluster.append(ln)
        placed = True
        break
    if not placed:
      clusters.append([ln])

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
      LineSegment(cx - dx, cy - dy, cx + dx, cy + dy, group=cluster[0].group)
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
  """Generate front-face candidate tuples: (AF, BE, AB, FE) line proxies.

  Requires at least 2 vertical and 2 front-horizontal lines.
  When 3+ verticals exist, the rightmost vertical is reserved for the
  right-face CD upgrade (not consumed as the front right edge).
  Bounded by cfg.max_front_candidates.
  """
  vertical = sorted(groups.vertical, key=_vertical_sort_key)
  fh = groups.front_horizontal
  if len(vertical) < 2 or len(fh) < 2:
    return []

  # Reserve the rightmost vertical for hex right-face CD when available
  max_x_ln = vertical[-1] if len(vertical) >= 3 else None

  candidates: list[tuple[LineSegment, LineSegment, LineSegment, LineSegment]] = []
  n = len(vertical)
  for i in range(n - 1):
    for j in range(i + 1, n):
      be = vertical[j]
      # Don't use the rightmost vertical as the front right edge when
      # there are 3+ verticals — reserve it for right-face CD.
      if max_x_ln is not None and be is max_x_ln:
        continue
      af = vertical[i]
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

  Requires at least 1 vertical (for CD) and 2 right-diagonal lines.
  Bounded by cfg.max_right_candidates.
  """
  vertical = sorted(groups.vertical, key=_vertical_sort_key)
  rd = groups.right_diagonal
  if len(vertical) < 1 or len(rd) < 2:
    return []

  candidates: list[tuple[LineSegment, LineSegment, LineSegment]] = []
  for cd in vertical:
    for bc in rd:
      for ed in rd:
        if bc is ed:
          continue
        candidates.append((cd, bc, ed))
        if len(candidates) >= cfg.max_right_candidates:
          return candidates
  return candidates


def pick_line_combinations(groups: LineGroups, cfg: HexDetectorConfig) -> list[tuple[LineSegment, ...]]:
  """Legacy wrapper: generate full 7-line candidate tuples (backward compat)."""
  vertical = sorted(groups.vertical, key=_vertical_sort_key)
  fh = groups.front_horizontal
  rd = groups.right_diagonal
  if len(vertical) < 3 or len(fh) < 2 or len(rd) < 2:
    return []

  candidates: list[tuple[LineSegment, ...]] = []
  n = len(vertical)
  for i in range(n - 2):
    for j in range(i + 1, n - 1):
      for k in range(j + 1, n):
        af, be, cd = vertical[i], vertical[j], vertical[k]
        for ab in fh:
          for fe in fh:
            if ab is fe:
              continue
            for bc in rd:
              for ed in rd:
                if bc is ed:
                  continue
                candidates.append((af, be, cd, ab, fe, bc, ed))
                if len(candidates) >= cfg.max_candidates:
                  return candidates
  return candidates

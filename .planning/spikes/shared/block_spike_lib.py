"""Shared utilities for block_detection_v2 spikes."""

from __future__ import annotations

import json
import math
import sys
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, List, Optional, Tuple

import cv2
import numpy as np

REPO_ROOT = Path(__file__).resolve().parents[3]
SRC_ROOT = REPO_ROOT / "src"
if str(SRC_ROOT) not in sys.path:
    sys.path.insert(0, str(SRC_ROOT))

from block_detection_v2.edges import detect_edges  # noqa: E402
from block_detection_v2.models import Point2D  # noqa: E402
from block_detection_v2.preprocessing import preprocess  # noqa: E402

Point = Tuple[float, float]
LineSegment = Tuple[Point, Point]
LABELS = "ABCDEF"


@dataclass
class ROIBox:
    x: int
    y: int
    w: int
    h: int
    mask: np.ndarray
    area: int
    block_mode: int = 3

    def as_tuple(self) -> Tuple[int, int, int, int]:
        return (self.x, self.y, self.w, self.h)


@dataclass
class SpikeEvent:
    ts: str
    category: str
    message: str
    data: dict = field(default_factory=dict)


class ForensicLog:
    def __init__(self, spike_id: str) -> None:
        self.spike_id = spike_id
        self.events: List[SpikeEvent] = []
        self.started = datetime.now(timezone.utc)

    def log(self, category: str, message: str, **data) -> None:
        self.events.append(
            SpikeEvent(
                ts=datetime.now(timezone.utc).isoformat(),
                category=category,
                message=message,
                data=data,
            )
        )

    def summary(self) -> dict:
        cats: Dict[str, int] = {}
        for e in self.events:
            cats[e.category] = cats.get(e.category, 0) + 1
        return {
            "spike_id": self.spike_id,
            "duration_s": (datetime.now(timezone.utc) - self.started).total_seconds(),
            "event_count": len(self.events),
            "categories": cats,
        }

    def export(self, path: Path) -> None:
        def _json_safe(obj):
            if isinstance(obj, dict):
                return {k: _json_safe(v) for k, v in obj.items()}
            if isinstance(obj, list):
                return [_json_safe(v) for v in obj]
            if isinstance(obj, (np.integer, np.int32, np.int64)):
                return int(obj)
            if isinstance(obj, (np.floating, np.float32, np.float64)):
                return float(obj)
            return obj

        payload = {"summary": self.summary(), "events": [e.__dict__ for e in self.events]}
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(_json_safe(payload), indent=2), encoding="utf-8")


def dataset_dir() -> Path:
    return SRC_ROOT / "block_detection_v2" / "block_dataset"


def list_dataset() -> List[Path]:
    return sorted(dataset_dir().glob("dt*.jpg"), key=lambda p: int(p.stem[2:]))


def _line_angle(p1: Point, p2: Point) -> float:
    return math.degrees(math.atan2(p2[1] - p1[1], p2[0] - p1[0])) % 180.0


def _line_length(p1: Point, p2: Point) -> float:
    return math.hypot(p2[0] - p1[0], p2[1] - p1[1])


def _dist(a: Point, b: Point) -> float:
    return math.hypot(a[0] - b[0], a[1] - b[1])


def _polygon_area(pts: List[Point]) -> float:
    if len(pts) < 3:
        return 0.0
    arr = np.array(pts, dtype=np.float64)
    x, arr_y = arr[:, 0], arr[:, 1]
    return float(0.5 * abs(np.dot(x, np.roll(arr_y, -1)) - np.dot(arr_y, np.roll(x, -1))))


def extract_cluster_roi(
    edges: np.ndarray,
    frame_shape: Tuple[int, int],
    *,
    block_mode: int = 3,
    pallet_frac: float = 0.78,
    log: Optional[ForensicLog] = None,
) -> Optional[ROIBox]:
    """Isolate block-cluster silhouette; trim right for 3-block mode."""
    h, w = frame_shape
    work = edges.copy()
    pallet_y = int(h * pallet_frac)
    work[pallet_y:, :] = 0

    kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (9, 9))
    merged = cv2.morphologyEx(work, cv2.MORPH_CLOSE, kernel, iterations=2)
    merged = cv2.dilate(merged, kernel, iterations=2)

    num, labels, stats, _ = cv2.connectedComponentsWithStats(merged)
    best_idx = -1
    best_score = 0.0
    for i in range(1, num):
        x, y, bw, bh, area = stats[i]
        if area < 800:
            continue
        cy = y + bh / 2.0
        if cy > h * 0.88:
            continue
        centrality = 1.0 - abs((x + bw / 2.0) - w / 2.0) / (w / 2.0)
        upper_bonus = 1.0 - (cy / h)
        score = area * (0.5 + 0.3 * centrality + 0.2 * upper_bonus)
        if score > best_score:
            best_score = score
            best_idx = i

    if best_idx < 0:
        if log:
            log.log("roi", "no_cluster_component")
        return None

    comp_mask = (labels == best_idx).astype(np.uint8) * 255
    x, y, bw, bh, area = stats[best_idx]

    pad = max(12, int(min(bw, bh) * 0.04))
    x0 = max(0, x - pad)
    y0 = max(0, y - pad)
    x1 = min(w, x + bw + pad)
    y1 = min(h, y + bh + pad)

    if block_mode == 3:
        full_w = x1 - x0
        trim = int(full_w * 0.22)
        x1 = max(x0 + int(full_w * 0.45), x1 - trim)

    roi_mask = np.zeros((h, w), dtype=np.uint8)
    roi_mask[y0:y1, x0:x1] = 255
    roi_mask = cv2.bitwise_and(roi_mask, comp_mask)
    roi_mask = cv2.dilate(roi_mask, cv2.getStructuringElement(cv2.MORPH_RECT, (5, 5)), 1)

    if log:
        log.log(
            "roi",
            "cluster_found",
            x=x0,
            y=y0,
            w=x1 - x0,
            h=y1 - y0,
            area=int(area),
            block_mode=block_mode,
        )

    return ROIBox(x=x0, y=y0, w=x1 - x0, h=y1 - y0, mask=roi_mask, area=int(area), block_mode=block_mode)


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


def _intersect_lines(l1: LineSegment, l2: LineSegment) -> Optional[Point]:
    (x1, y1), (x2, y2) = l1
    (x3, y3), (x4, y4) = l2
    denom = (x1 - x2) * (y3 - y4) - (y1 - y2) * (x3 - x4)
    if abs(denom) < 1e-6:
        return None
    px = ((x1 * y2 - y1 * x2) * (x3 - x4) - (x1 - x2) * (x3 * y4 - y3 * x4)) / denom
    py = ((x1 * y2 - y1 * x2) * (y3 - y4) - (y1 - y2) * (x3 * y4 - y3 * x4)) / denom
    return (px, py)


def _pick_line_near_angle(lines: List[LineSegment], target_deg: float, tol: float = 20.0) -> Optional[LineSegment]:
    best = None
    best_d = 999.0
    for seg in lines:
        ang = _line_angle(seg[0], seg[1])
        d = min(abs(ang - target_deg), abs(ang - target_deg - 180))
        if d < tol and d < best_d:
            best_d = d
            best = seg
    return best


def _dominant_angles(lines: List[LineSegment], bins: int = 18) -> List[float]:
    if not lines:
        return []
    hist = [0.0] * bins
    for p1, p2 in lines:
        ang = _line_angle(p1, p2)
        bucket = int(ang / (180.0 / bins)) % bins
        hist[bucket] += _line_length(p1, p2)
    peaks: List[float] = []
    for i, weight in enumerate(hist):
        left = hist[(i - 1) % bins]
        right = hist[(i + 1) % bins]
        if weight >= left and weight >= right and weight > 0:
            peaks.append((i * (180.0 / bins) + (180.0 / bins) / 2.0, weight))
    peaks.sort(key=lambda x: x[1], reverse=True)
    return [p[0] for p in peaks[:4]]


def _hex_from_roi(roi: ROIBox) -> Dict[str, Point2D]:
    """Seed A–F from ROI box with 3-block isometric proportions."""
    x, y, w, h = roi.x, roi.y, roi.w, roi.h
    inset_x = w * 0.06
    inset_y = h * 0.08
    mid_x = x + w * 0.52
    a = (x + inset_x, y + inset_y)
    c = (x + w - inset_x, y + inset_y + h * 0.04)
    f = (x + inset_x, y + h - inset_y)
    d = (x + w - inset_x, y + h - inset_y)
    b = (mid_x - w * 0.02, y + inset_y + h * 0.02)
    e = (mid_x - w * 0.02, y + h - inset_y - h * 0.02)
    return {
        "A": Point2D(*a),
        "B": Point2D(*b),
        "C": Point2D(*c),
        "D": Point2D(*d),
        "E": Point2D(*e),
        "F": Point2D(*f),
    }


def _snap_point_to_edges(pt: Point, edges: np.ndarray, radius: int = 12) -> Point:
    h, w = edges.shape[:2]
    cx, cy = int(pt[0]), int(pt[1])
    best = pt
    best_val = -1
    for dy in range(-radius, radius + 1):
        for dx in range(-radius, radius + 1):
            x, y = cx + dx, cy + dy
            if 0 <= x < w and 0 <= y < h and edges[y, x] > best_val:
                best_val = int(edges[y, x])
                best = (float(x), float(y))
    return best


def _refine_with_lines(
    seed: Dict[str, Point2D],
    lines: List[LineSegment],
    edges: np.ndarray,
    roi: ROIBox,
) -> Dict[str, Point2D]:
    merged = _merge_lines_by_angle(lines, angle_tol=10.0)
    angles = _dominant_angles(merged)
    if len(angles) < 2:
        return {k: Point2D(*_snap_point_to_edges(v.as_tuple(), edges)) for k, v in seed.items()}

    top_angle = min(angles, key=lambda a: min(abs(a - 0), abs(a - 180), abs(a - 90)))
    diag_angle = max(angles, key=lambda a: abs(a - 35))

    top = _pick_line_near_angle(merged, top_angle, 25) or _pick_line_near_angle(merged, 0, 30)
    diag = _pick_line_near_angle(merged, diag_angle, 25) or _pick_line_near_angle(merged, 35, 25)
    left = ((roi.x, roi.y + roi.h * 0.1), (roi.x, roi.y + roi.h * 0.9))
    right = ((roi.x + roi.w, roi.y + roi.h * 0.1), (roi.x + roi.w, roi.y + roi.h * 0.9))

    refined = dict(seed)
    if top and diag:
        b_hit = _intersect_lines(top, diag)
        if b_hit:
            refined["B"] = Point2D(*_snap_point_to_edges(b_hit, edges))
    if top:
        a_hit = _intersect_lines(top, left)
        c_hit = _intersect_lines(top, right)
        if a_hit:
            refined["A"] = Point2D(*_snap_point_to_edges(a_hit, edges))
        if c_hit:
            refined["C"] = Point2D(*_snap_point_to_edges(c_hit, edges))
    if diag:
        e_hit = _intersect_lines(diag, ((roi.x, roi.y + roi.h * 0.55), (roi.x + roi.w, roi.y + roi.h * 0.55)))
        if e_hit:
            refined["E"] = Point2D(*_snap_point_to_edges(e_hit, edges))

    for label in LABELS:
        refined[label] = Point2D(*_snap_point_to_edges(refined[label].as_tuple(), edges))
    return refined


def fit_hexagon_from_lines(
    lines: List[LineSegment],
    roi: ROIBox,
    frame_shape: Tuple[int, int],
    edges: Optional[np.ndarray] = None,
    log: Optional[ForensicLog] = None,
) -> Optional[Dict[str, Point2D]]:
    """Fit A–F from ROI seed + line refinement (topology-aware)."""
    seed = _hex_from_roi(roi)
    if edges is None:
        edges = np.zeros(frame_shape, dtype=np.uint8)

    points = _refine_with_lines(seed, lines, edges, roi)

    if not validate_topology(points, strict=False):
        if log:
            log.log("fit", "topology_reject_relaxed", lines_in=len(lines))
        points = seed

    if not validate_topology(points, strict=False):
        if log:
            log.log("fit", "topology_reject_final")
        return None

    if log:
        log.log("fit", "hexagon_fitted", lines_in=len(lines), dominant=len(_dominant_angles(_merge_lines_by_angle(lines))))
    return points


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
    if hex_area < 3500:
        return 0.0
    # Penalize tiny relative to ROI (label/logo pattern)
    if area_ratio < 0.12:
        return 0.0
    return float(0.35 * area_ratio + 0.45 * support + 0.20 * topo)


def draw_hexagon(
    img: np.ndarray,
    points: Dict[str, Point2D],
    color: Tuple[int, int, int] = (0, 255, 0),
    thickness: int = 2,
) -> None:
    order = ["A", "B", "C", "D", "E", "F", "A"]
    arr = np.array([[int(points[k].x), int(points[k].y)] for k in order], dtype=np.int32)
    cv2.polylines(img, [arr], False, color, thickness)
    for label in LABELS:
        pt = points[label]
        cv2.circle(img, (int(pt.x), int(pt.y)), 4, color, -1)
        cv2.putText(img, label, (int(pt.x) + 4, int(pt.y) - 4), cv2.FONT_HERSHEY_SIMPLEX, 0.45, (255, 255, 255), 1)


def draw_roi(img: np.ndarray, roi: ROIBox, color: Tuple[int, int, int] = (255, 180, 0)) -> None:
    overlay = img.copy()
    overlay[roi.mask > 0] = (
        overlay[roi.mask > 0] * 0.55 + np.array(color) * 0.45
    ).astype(np.uint8)
    cv2.addWeighted(overlay, 0.7, img, 0.3, 0, img)
    cv2.rectangle(img, (roi.x, roi.y), (roi.x + roi.w, roi.y + roi.h), color, 2)
    cv2.putText(
        img,
        f"ROI {roi.block_mode}-block",
        (roi.x, max(20, roi.y - 8)),
        cv2.FONT_HERSHEY_SIMPLEX,
        0.55,
        color,
        2,
    )


def process_image(path: Path, log: Optional[ForensicLog] = None) -> dict:
    frame = cv2.imread(str(path))
    if frame is None:
        return {"file": path.name, "ok": False, "error": "read_failed"}

    color, gray = preprocess(frame)
    edges, lines = detect_edges(gray)
    roi = extract_cluster_roi(edges, color.shape[:2], block_mode=3, log=log)
    if roi is None:
        return {"file": path.name, "ok": False, "stage": "roi", "lines": len(lines)}

    masked_edges = cv2.bitwise_and(edges, roi.mask)
    roi_lines = []
    for p1, p2 in lines:
        mx = (p1[0] + p2[0]) / 2.0
        my = (p1[1] + p2[1]) / 2.0
        if roi.mask[int(my), int(mx)] > 0:
            roi_lines.append((p1, p2))

    points = fit_hexagon_from_lines(roi_lines or lines, roi, color.shape[:2], edges=masked_edges, log=log)
    if points is None:
        return {"file": path.name, "ok": False, "stage": "fit", "lines": len(lines), "roi_lines": len(roi_lines)}

    score = score_candidate(points, masked_edges, roi, strict_topology=True)
    return {
        "file": path.name,
        "ok": score >= 0.42,
        "score": score,
        "lines": len(lines),
        "roi_lines": len(roi_lines),
        "roi_area": roi.area,
        "hex_area": _polygon_area([points[k].as_tuple() for k in LABELS]),
        "edge_support": edge_support(points, masked_edges),
        "points": {k: [points[k].x, points[k].y] for k in LABELS},
    }

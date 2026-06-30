from __future__ import annotations

import math
from typing import Dict, List, Tuple

import cv2
import numpy as np

from .models import GeometryResult, Point2D

Point = Tuple[float, float]


def _dist(a: Point2D, b: Point2D) -> float:
    return math.hypot(a.x - b.x, a.y - b.y)


def _to_np(pts: List[Point2D]) -> np.ndarray:
    return np.array([[p.x, p.y] for p in pts], dtype=np.float32)


def _quad_warp_lines(
    src_quad: List[Point2D],
    out_w: int,
    out_h: int,
) -> Tuple[List[Tuple[Point, Point]], List[Tuple[Point, Point]]]:
    src = _to_np(src_quad)
    dst = np.array([[0, 0], [out_w - 1, 0], [out_w - 1, out_h - 1], [0, out_h - 1]], dtype=np.float32)
    h_mat = cv2.getPerspectiveTransform(src, dst)

    mid_top = ((src_quad[0].x + src_quad[1].x) / 2, (src_quad[0].y + src_quad[1].y) / 2)
    mid_bot = ((src_quad[3].x + src_quad[2].x) / 2, (src_quad[3].y + src_quad[2].y) / 2)

    split_dst = np.array([[[out_w / 2, 0]], [[out_w / 2, out_h - 1]]], dtype=np.float32)
    split_src = cv2.perspectiveTransform(split_dst, cv2.invert(h_mat)[1])
    p1 = (float(split_src[0][0][0]), float(split_src[0][0][1]))
    p2 = (float(split_src[1][0][0]), float(split_src[1][0][1]))
    split_line = (p1, p2)

    block_lines: List[Tuple[Point, Point]] = [split_line]
    for frac in (0.25, 0.75):
        y = out_h * frac
        row_dst = np.array([[[0, y]], [[out_w - 1, y]]], dtype=np.float32)
        row_src = cv2.perspectiveTransform(row_dst, cv2.invert(h_mat)[1])
        block_lines.append(
            (
                (float(row_src[0][0][0]), float(row_src[0][0][1])),
                (float(row_src[1][0][0]), float(row_src[1][0][1])),
            )
        )

    return [split_line], block_lines


def compute_geometry(points: Dict[str, Point2D]) -> GeometryResult:
    a, b, c, d, e, f = (points[k] for k in "ABCDEF")

    front_face = [a, b, e, f]
    right_face = [b, c, d, e]

    w_front = (_dist(a, b) + _dist(f, e)) / 2.0
    w_right = (_dist(b, c) + _dist(e, d)) / 2.0
    yaw_deg = math.degrees(math.atan2(w_right, w_front)) if w_front > 1e-6 else 0.0

    cx = sum(p.x for p in points.values()) / 6.0
    cy = sum(p.y for p in points.values()) / 6.0
    center = Point2D(cx, cy)

    fw = max(int(w_front), 40)
    rh = max(int((_dist(b, e) + _dist(a, f)) / 2.0), 40)
    front_splits, front_blocks = _quad_warp_lines(front_face, fw, rh)

    rw = max(int(w_right), 40)
    right_splits, right_blocks = _quad_warp_lines(right_face, rw, rh)

    block_lines = front_blocks + right_blocks

    return GeometryResult(
        front_face=front_face,
        right_face=right_face,
        front_width=w_front,
        right_width=w_right,
        yaw_deg=yaw_deg,
        center=center,
        front_split_lines=front_splits,
        right_split_lines=right_splits,
        block_lines=block_lines,
    )

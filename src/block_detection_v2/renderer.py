from __future__ import annotations

from typing import Dict, List, Optional

import cv2
import numpy as np

from . import config
from .models import BlockResult, GeometryResult, HexagonDetection

_COLORS = [
    (0, 255, 255),
    (0, 255, 0),
    (255, 128, 0),
    (255, 0, 255),
    (0, 200, 255),
    (180, 255, 0),
]


def _draw_polyline(img: np.ndarray, pts, color, thickness: int = 2) -> None:
    arr = np.array([[int(p.x), int(p.y)] for p in pts], dtype=np.int32)
    cv2.polylines(img, [arr], True, color, thickness)


def _draw_block(
    out: np.ndarray,
    detection: HexagonDetection,
    geometry: Optional[GeometryResult],
    color: tuple[int, int, int],
    block_id: int,
) -> None:
    order = ["A", "B", "C", "D", "E", "F", "A"]
    poly_pts = [detection.points[k] for k in order]
    _draw_polyline(out, poly_pts, color, 2)

    for label, pt in detection.points.items():
        px, py = int(pt.x), int(pt.y)
        cv2.circle(out, (px, py), 4, color, -1)
        cv2.putText(out, label, (px + 5, py - 5), cv2.FONT_HERSHEY_SIMPLEX, 0.45, (255, 255, 255), 1)

    if geometry is not None:
        _draw_polyline(out, geometry.front_face, color, 1)
        _draw_polyline(out, geometry.right_face, color, 1)
        for line in geometry.block_lines:
            p1 = (int(line[0][0]), int(line[0][1]))
            p2 = (int(line[1][0]), int(line[1][1]))
            cv2.line(out, p1, p2, color, 1, cv2.LINE_AA)
        cx, cy = int(geometry.center.x), int(geometry.center.y)
        cv2.drawMarker(out, (cx, cy), color, cv2.MARKER_CROSS, 12, 2)
        cv2.putText(
            out,
            f"#{block_id} yaw {geometry.yaw_deg:.0f}",
            (cx + 8, cy - 8),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.45,
            color,
            1,
        )


def render(
    frame: np.ndarray,
    blocks: List[BlockResult],
    fps: float,
    detected: bool,
    hint: str = "",
    *,
    yolo_boxes: Optional[List[dict]] = None,
) -> np.ndarray:
    out = frame.copy()

    if config.DEBUG_YOLO and yolo_boxes:
        for box in yolo_boxes:
            xyxy = box.get("xyxy", [])
            if len(xyxy) == 4:
                x1, y1, x2, y2 = (int(v) for v in xyxy)
                cv2.rectangle(out, (x1, y1), (x2, y2), (0, 140, 255), 2)

    for i, block in enumerate(blocks):
        color = _COLORS[i % len(_COLORS)]
        det = HexagonDetection(points=block.points, contour_area=0.0, score=block.score)
        _draw_block(out, det, block.geometry, color, i + 1)

    status = "detected" if detected else "lost"
    color = (0, 220, 0) if detected else (0, 0, 220)
    cv2.putText(out, f"status: {status}  blocks: {len(blocks)}", (12, 28), cv2.FONT_HERSHEY_SIMPLEX, 0.7, color, 2)
    cv2.putText(out, f"fps: {fps:.1f}", (12, 56), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2)
    if hint:
        cv2.putText(out, hint, (12, 84), cv2.FONT_HERSHEY_SIMPLEX, 0.55, (200, 200, 200), 1)

    return out


def frame_output(blocks: List[BlockResult]) -> Dict:
    if not blocks:
        return {
            "detected": False,
            "blocks": [],
            "points": {k: [0.0, 0.0] for k in "ABCDEF"},
            "center": [0.0, 0.0],
            "front_width": 0.0,
            "right_width": 0.0,
            "yaw_deg": 0.0,
        }

    first = blocks[0]
    return {
        "detected": True,
        "blocks": [
            {
                "points": {k: b.points[k].as_list() for k in "ABCDEF"},
                "center": b.center.as_list(),
                "front_width": b.front_width,
                "right_width": b.right_width,
                "yaw_deg": b.yaw_deg,
                "score": b.score,
            }
            for b in blocks
        ],
        "points": {k: first.points[k].as_list() for k in "ABCDEF"},
        "center": first.center.as_list(),
        "front_width": first.front_width,
        "right_width": first.right_width,
        "yaw_deg": first.yaw_deg,
    }

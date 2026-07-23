"""Draw shortest path line from camera center to target block."""

from __future__ import annotations

import math
from typing import Any

import cv2
import numpy as np


def _arrow_head(
    tip: tuple[int, int],
    angle_rad: float,
    length: int = 20,
    spread_deg: float = 30.0,
) -> list[tuple[int, int]]:
    """Compute arrowhead polygon points."""
    spread = math.radians(spread_deg)
    a1 = angle_rad + math.pi - spread
    a2 = angle_rad + math.pi + spread
    p1 = (int(tip[0] + length * math.cos(a1)), int(tip[1] + length * math.sin(a1)))
    p2 = (int(tip[0] + length * math.cos(a2)), int(tip[1] + length * math.sin(a2)))
    return [tip, p1, p2]


def draw_path_to_target(
    frame: Any,
    target_center: tuple[float, float],
    camera_center: tuple[float, float],
    distance_cm: float | None = None,
    *,
    line_color: tuple[int, int, int] = (255, 191, 0),  # BGR: Amber
    arrow_color: tuple[int, int, int] = (0, 165, 255),  # BGR: Orange
    thickness: int = 2,
    arrow_size: int = 18,
) -> None:
    """Draw shortest path line + arrow from camera center to target.

    Args:
        frame: Image to draw on (mutated in-place).
        target_center: (cx, cy) of detected block center.
        camera_center: (cx, cy) of camera frame center.
        distance_cm: Optional estimated distance in cm for label.
        line_color: BGR color for the path line.
        arrow_color: BGR color for the arrowhead.
        thickness: Line thickness.
        arrow_size: Arrowhead size in pixels.
    """
    tx, ty = int(target_center[0]), int(target_center[1])
    cx, cy = int(camera_center[0]), int(camera_center[1])

    # --- Dashed line ---
    # Draw alternating segments for a dashed effect
    dash_len = 12
    gap_len = 8
    dx = tx - cx
    dy = ty - cy
    total = math.hypot(dx, dy)
    if total < 2:
        return  # too close to draw

    steps = int(total / (dash_len + gap_len))
    for i in range(steps):
        t0 = i * (dash_len + gap_len) / total
        t1 = min(t0 + dash_len / total, 1.0)
        p0 = (int(cx + dx * t0), int(cy + dy * t0))
        p1 = (int(cx + dx * t1), int(cy + dy * t1))
        cv2.line(frame, p0, p1, line_color, thickness, cv2.LINE_AA)

    # --- Arrowhead at target ---
    angle = math.atan2(ty - cy, tx - cx)
    pts = _arrow_head((tx, ty), angle, length=arrow_size)
    pts_array = np.array(pts, dtype=np.int32).reshape((-1, 1, 2))
    cv2.fillPoly(frame, [pts_array], arrow_color)

    # --- Distance label ---
    if distance_cm is not None:
        mid_x = int((cx + tx) / 2)
        mid_y = int((cy + ty) / 2)
        label = f"{distance_cm:.1f}cm"
        cv2.putText(
            frame,
            label,
            (mid_x + 8, mid_y - 8),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.5,
            (255, 255, 255),
            1,
            cv2.LINE_AA,
        )


def draw_robot_status(
    frame: Any,
    status_text: str,
    *,
    color: tuple[int, int, int] = (0, 255, 200),
    font_scale: float = 0.6,
) -> None:
    """Draw robot navigation status text at top-right of frame."""
    h, w = frame.shape[:2]
    (text_w, _), _ = cv2.getTextSize(status_text, cv2.FONT_HERSHEY_SIMPLEX, font_scale, 2)
    x = w - text_w - 16
    y = 28
    # Background box
    cv2.rectangle(frame, (x - 6, y - 20), (w - 4, y + 8), (20, 20, 20), -1)
    cv2.putText(
        frame,
        status_text,
        (x, y),
        cv2.FONT_HERSHEY_SIMPLEX,
        font_scale,
        color,
        2,
        cv2.LINE_AA,
    )

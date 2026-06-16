"""Pure geometry helpers (no model dependencies)."""

import math

from block_detected.core.types import Box


def point_in_rect(x: int, y: int, rect: tuple[int, int, int, int]) -> bool:
    x1, y1, x2, y2 = rect
    return x1 <= x <= x2 and y1 <= y <= y2


def box_area(box: Box) -> int:
    x1, y1, x2, y2 = box
    width = max(0, x2 - x1)
    height = max(0, y2 - y1)
    return width * height


def intersection_area(a: Box, b: Box) -> int:
    ax1, ay1, ax2, ay2 = a
    bx1, by1, bx2, by2 = b
    ix1 = max(ax1, bx1)
    iy1 = max(ay1, by1)
    ix2 = min(ax2, bx2)
    iy2 = min(ay2, by2)
    if ix2 <= ix1 or iy2 <= iy1:
        return 0
    return (ix2 - ix1) * (iy2 - iy1)


def iou(a: Box, b: Box) -> float:
    inter = intersection_area(a, b)
    if inter == 0:
        return 0.0
    union = box_area(a) + box_area(b) - inter
    if union <= 0:
        return 0.0
    return inter / union


def box_center(box: Box) -> tuple[float, float]:
    """Calculate center (cx, cy) of a box (x1, y1, x2, y2)."""
    x1, y1, x2, y2 = box
    cx = (x1 + x2) / 2.0
    cy = (y1 + y2) / 2.0
    return cx, cy


def box_to_xywh(box: Box) -> tuple[float, float, float, float]:
    """Convert box (x1, y1, x2, y2) to XYWH (x, y, width, height)."""
    x1, y1, x2, y2 = box
    x = x1
    y = y1
    w = x2 - x1
    h = y2 - y1
    return x, y, w, h


def distance_between_points(
    point1: tuple[float, float],
    point2: tuple[float, float],
) -> float:
    """Calculate Euclidean distance between two points."""
    x1, y1 = point1
    x2, y2 = point2
    return math.sqrt((x2 - x1) ** 2 + (y2 - y1) ** 2)


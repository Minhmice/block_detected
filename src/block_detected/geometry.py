"""GEO-03/04/05: corner ordering, perspective warp, center and angle."""

from __future__ import annotations

import math
from dataclasses import dataclass

import cv2
import numpy as np

from .detection_contract import CornersPx, PointPx
from .detector import SquareCandidate

DEFAULT_WARP_SIZE = 128


@dataclass(frozen=True)
class GeometrySettings:
    warp_size: int = DEFAULT_WARP_SIZE

    def __post_init__(self) -> None:
        if self.warp_size < 32 or self.warp_size > 256:
            raise ValueError("warp_size must be between 32 and 256")


@dataclass(frozen=True)
class FaceGeometry:
    corners_px: CornersPx
    center_px: PointPx
    angle_deg: float
    warped_bgr: np.ndarray


def order_corners_tl_tr_br_bl(approx_xy: np.ndarray) -> CornersPx:
    """Order four unordered vertices to TL, TR, BR, BL (image coords, y down)."""
    pts = np.asarray(approx_xy, dtype=np.float64).reshape(4, 2)
    if pts.shape != (4, 2):
        raise ValueError(f"expected four (x, y) points; got shape {pts.shape!r}")

    by_y = pts[np.argsort(pts[:, 1])]
    top = by_y[:2]
    bottom = by_y[2:]
    top = top[np.argsort(top[:, 0])]
    bottom = bottom[np.argsort(bottom[:, 0])]
    tl, tr = top[0], top[1]
    bl, br = bottom[0], bottom[1]

    return CornersPx(
        top_left=PointPx(float(tl[0]), float(tl[1])),
        top_right=PointPx(float(tr[0]), float(tr[1])),
        bottom_right=PointPx(float(br[0]), float(br[1])),
        bottom_left=PointPx(float(bl[0]), float(bl[1])),
    )


def compute_center_and_angle(corners: CornersPx) -> tuple[PointPx, float]:
    """Center is mean of corners; angle is atan2(TR - TL) in degrees."""
    tl, tr, br, bl = corners.as_ordered_tuple()
    cx = (tl.x + tr.x + br.x + bl.x) / 4.0
    cy = (tl.y + tr.y + br.y + bl.y) / 4.0
    angle_rad = math.atan2(tr.y - tl.y, tr.x - tl.x)
    return PointPx(cx, cy), math.degrees(angle_rad)


def warp_face_bgr(
    frame_bgr: np.ndarray,
    corners: CornersPx,
    warp_size: int = DEFAULT_WARP_SIZE,
) -> np.ndarray:
    """Perspective-warp the quad face to a canonical square BGR crop."""
    tl, tr, br, bl = corners.as_ordered_tuple()
    src = np.array(
        [
            [tl.x, tl.y],
            [tr.x, tr.y],
            [br.x, br.y],
            [bl.x, bl.y],
        ],
        dtype=np.float32,
    )
    dst = np.array(
        [
            [0, 0],
            [warp_size - 1, 0],
            [warp_size - 1, warp_size - 1],
            [0, warp_size - 1],
        ],
        dtype=np.float32,
    )
    matrix = cv2.getPerspectiveTransform(src, dst)
    warped = cv2.warpPerspective(frame_bgr, matrix, (warp_size, warp_size))
    return np.ascontiguousarray(warped, dtype=np.uint8)


def validate_quad_geometry(
    corners: CornersPx,
    *,
    min_interior_angle_deg: float = 60.0,
    max_interior_angle_deg: float = 120.0,
) -> bool:
    """Return False when corner angles are too skewed for a square face."""
    pts = np.array(
        [
            [corners.top_left.x, corners.top_left.y],
            [corners.top_right.x, corners.top_right.y],
            [corners.bottom_right.x, corners.bottom_right.y],
            [corners.bottom_left.x, corners.bottom_left.y],
        ],
        dtype=np.float64,
    )
    n = len(pts)
    for i in range(n):
        p0 = pts[(i - 1) % n]
        p1 = pts[i]
        p2 = pts[(i + 1) % n]
        v1 = p0 - p1
        v2 = p2 - p1
        denom = float(np.linalg.norm(v1) * np.linalg.norm(v2))
        if denom < 1e-6:
            return False
        cos_angle = float(np.clip(np.dot(v1, v2) / denom, -1.0, 1.0))
        angle = math.degrees(math.acos(cos_angle))
        if angle < min_interior_angle_deg or angle > max_interior_angle_deg:
            return False
    return True


def geometry_from_candidate(
    candidate: SquareCandidate,
    frame_bgr: np.ndarray,
    settings: GeometrySettings | None = None,
) -> FaceGeometry:
    """Build ordered corners, pose metrics, and warped crop from one detector candidate."""
    settings = settings or GeometrySettings()
    corners = order_corners_tl_tr_br_bl(candidate.approx_xy)
    center_px, angle_deg = compute_center_and_angle(corners)
    warped = warp_face_bgr(frame_bgr, corners, settings.warp_size)
    return FaceGeometry(
        corners_px=corners,
        center_px=center_px,
        angle_deg=angle_deg,
        warped_bgr=warped,
    )

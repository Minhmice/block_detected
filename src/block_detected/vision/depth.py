"""Distance estimation from monocular camera — pixel diagonal → cm.

Uses bounding box DIAGONAL instead of width → rotation-invariant for square blocks.
Focal length auto-computed from HFOV + frame width (no manual calibration needed).
"""

from __future__ import annotations

import math
import logging

from block_detected.core.domain import Detection
from block_detected.core.types import Box

logger = logging.getLogger(__name__)

# Pi Camera v3 wide: HFOV ~66° (diagonal ~75°)
DEFAULT_HFOV_DEG: float = 66.0

# Block 4×4 cm → real diagonal = 4 * √2 ≈ 5.657 cm
DEFAULT_BLOCK_SIZE_CM: float = 4.0

# Sanity bounds
MIN_DISTANCE_CM: float = 0.5
MAX_DISTANCE_CM: float = 500.0


def calc_focal_length_px(frame_width: float, hfov_deg: float) -> float:
    """Compute focal length in pixels from camera HFOV and frame width.

    F = (W / 2) / tan(HFOV / 2)

    Args:
        frame_width: Frame width in pixels (e.g. 1280).
        hfov_deg: Horizontal field of view in degrees (e.g. 66).

    Returns:
        Focal length in pixels.
    """
    half_fov = math.radians(hfov_deg / 2.0)
    return (frame_width / 2.0) / math.tan(half_fov)


def _box_diagonal_px(box: Box) -> float:
    """Pixel diagonal of bounding box: sqrt(w² + h²)."""
    x1, y1, x2, y2 = box
    w = float(x2 - x1)
    h = float(y2 - y1)
    return math.sqrt(w * w + h * h)


def _real_diagonal_cm(block_width_cm: float) -> float:
    """Real-world diagonal of a square block: side * sqrt(2)."""
    return block_width_cm * math.sqrt(2.0)


def estimate_distance_cm(
    box: Box,
    frame_width: int,
    *,
    block_width_cm: float = DEFAULT_BLOCK_SIZE_CM,
    hfov_deg: float = DEFAULT_HFOV_DEG,
) -> float:
    """Estimate distance from camera to square block using pinhole model.

    Uses bounding box DIAGONAL (rotation-invariant for square blocks):
        pixel_diag = sqrt(w² + h²)
        real_diag  = block_width_cm * sqrt(2)
        F          = (frame_width / 2) / tan(hfov / 2)
        distance   = F * real_diag / pixel_diag

    Args:
        box: (x1, y1, x2, y2) bounding box.
        frame_width: Camera frame width in pixels.
        block_width_cm: Real-world side length of square block in cm (default 4.0).
        hfov_deg: Camera horizontal FOV in degrees (default 66).

    Returns:
        Estimated distance in cm, clamped to [0.5, 500].
    """
    pixel_diag = _box_diagonal_px(box)

    if pixel_diag < 2.0:
        return MAX_DISTANCE_CM

    F = calc_focal_length_px(float(frame_width), hfov_deg)
    real_diag = _real_diagonal_cm(block_width_cm)
    distance = (F * real_diag) / pixel_diag
    return max(MIN_DISTANCE_CM, min(MAX_DISTANCE_CM, round(distance, 1)))


def estimate_distance_from_detection(
    detection: Detection,
    frame_width: int,
    *,
    block_width_cm: float = DEFAULT_BLOCK_SIZE_CM,
    hfov_deg: float = DEFAULT_HFOV_DEG,
) -> float:
    """Convenience wrapper: Detection → distance_cm."""
    return estimate_distance_cm(
        detection.box,
        frame_width=frame_width,
        block_width_cm=block_width_cm,
        hfov_deg=hfov_deg,
    )


def pixel_offset_to_angle(
    pixel_offset_x: float,
    frame_width: int,
    hfov_deg: float = DEFAULT_HFOV_DEG,
) -> float:
    """Convert horizontal pixel offset from center → yaw angle in degrees.

    angle = atan(offset * tan(hfov/2) / (W/2))

    Args:
        pixel_offset_x: Horizontal offset from frame center (px).
                        Positive = right, negative = left.
        frame_width: Frame width in pixels.
        hfov_deg: Horizontal field of view in degrees.

    Returns:
        Yaw angle in degrees. Positive = target is right of camera center.
    """
    fraction = pixel_offset_x / (frame_width / 2.0)
    fraction = max(-1.0, min(1.0, fraction))
    half_fov = math.radians(hfov_deg / 2.0)
    return math.degrees(math.atan(fraction * math.tan(half_fov)))

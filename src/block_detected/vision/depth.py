"""Distance estimation from monocular camera — pixel width → cm."""

from __future__ import annotations

import logging
from typing import Any

from block_detected.core.domain import Detection
from block_detected.core.types import Box

logger = logging.getLogger(__name__)

# Default calibration: focal length (px) × real object width (cm)
# Focal length = (pixel_width × known_distance) / real_width
# Pre-calibrated at 30cm distance with 5cm block → ~280px width on 640px frame
#   F = (280 * 30) / 5 = 1680
DEFAULT_FOCAL_LENGTH_PX: float = 1680.0

# Real width of a Lego/block in cm
DEFAULT_BLOCK_WIDTH_CM: float = 5.0

# Min/max sanity bounds
MIN_DISTANCE_CM: float = 0.5
MAX_DISTANCE_CM: float = 500.0


def estimate_distance_cm(
    box: Box,
    frame_width: int,
    *,
    focal_length_px: float = DEFAULT_FOCAL_LENGTH_PX,
    block_width_cm: float = DEFAULT_BLOCK_WIDTH_CM,
) -> float:
    """Estimate distance from camera to object using pinhole model.

    distance = (focal_length_px * block_width_cm) / pixel_width

    Args:
        box: (x1, y1, x2, y2) bounding box.
        frame_width: Width of camera frame in pixels.
        focal_length_px: Calibrated focal length in pixels.
        block_width_cm: Real-world object width in cm.

    Returns:
        Estimated distance in cm, clamped to [MIN_DISTANCE_CM, MAX_DISTANCE_CM].
    """
    x1, _y1, x2, _y2 = box
    pixel_width = float(x2 - x1)

    if pixel_width < 1.0:
        return MAX_DISTANCE_CM

    distance = (focal_length_px * block_width_cm) / pixel_width
    return max(MIN_DISTANCE_CM, min(MAX_DISTANCE_CM, round(distance, 1)))


def estimate_distance_from_detection(
    detection: Detection,
    frame_width: int,
    *,
    focal_length_px: float = DEFAULT_FOCAL_LENGTH_PX,
    block_width_cm: float = DEFAULT_BLOCK_WIDTH_CM,
) -> float:
    """Convenience wrapper: Detection → distance_cm."""
    return estimate_distance_cm(
        detection.box,
        frame_width=frame_width,
        focal_length_px=focal_length_px,
        block_width_cm=block_width_cm,
    )


def pixel_offset_to_angle(
    pixel_offset_x: float,
    frame_width: int,
    hfov_deg: float = 62.0,
) -> float:
    """Convert horizontal pixel offset from center → yaw angle in degrees.

    Args:
        pixel_offset_x: Horizontal offset from frame center (px).
                        Positive = right, negative = left.
        frame_width: Frame width in pixels.
        hfov_deg: Horizontal field of view in degrees (default ~62° for Pi cam v3).

    Returns:
        Yaw angle in degrees. Positive = target is right of center.
    """
    import math
    fraction = pixel_offset_x / (frame_width / 2.0)
    fraction = max(-1.0, min(1.0, fraction))
    half_fov = math.radians(hfov_deg / 2.0)
    return math.degrees(math.atan(fraction * math.tan(half_fov)))

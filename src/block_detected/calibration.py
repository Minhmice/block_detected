"""POSE-01/02: table homography and robot pickup pose from pixel geometry."""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Optional

import numpy as np

from .detection_contract import PickupPose, PointPx


@dataclass(frozen=True)
class CalibrationSettings:
    homography: Optional[tuple[tuple[float, float, float], ...]] = None
    origin_x_mm: float = 0.0
    origin_y_mm: float = 0.0
    gripper_offset_mm: float = 0.0

    def __post_init__(self) -> None:
        if self.homography is not None and len(self.homography) != 3:
            raise ValueError("homography must be 3×3")


def load_calibration_settings(path: str | Path) -> CalibrationSettings:
    """Load calibration JSON (homography + origin offsets)."""
    data = json.loads(Path(path).read_text(encoding="utf-8"))
    homography = None
    if "homography" in data:
        homography = tuple(tuple(row) for row in data["homography"])
    return CalibrationSettings(
        homography=homography,
        origin_x_mm=float(data.get("origin_x_mm", 0.0)),
        origin_y_mm=float(data.get("origin_y_mm", 0.0)),
        gripper_offset_mm=float(data.get("gripper_offset_mm", 0.0)),
    )


def pixel_to_pickup_pose(
    center_px: PointPx,
    angle_deg: float,
    calibration: CalibrationSettings,
) -> Optional[PickupPose]:
    """Convert pixel center + face angle to robot mm pose when homography is configured."""
    if calibration.homography is None:
        return None

    h = np.array(calibration.homography, dtype=np.float64)
    pt = np.array([center_px.x, center_px.y, 1.0], dtype=np.float64)
    mapped = h @ pt
    if abs(mapped[2]) < 1e-9:
        return None
    x_mm = float(mapped[0] / mapped[2]) + calibration.origin_x_mm
    y_mm = float(mapped[1] / mapped[2]) + calibration.origin_y_mm + calibration.gripper_offset_mm
    return PickupPose(x_mm=x_mm, y_mm=y_mm, theta_deg=float(angle_deg))

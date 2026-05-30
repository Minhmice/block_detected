"""Calibration and pose conversion tests."""

from __future__ import annotations

import json
from pathlib import Path

from block_detected.calibration import CalibrationSettings, load_calibration_settings, pixel_to_pickup_pose
from block_detected.detection_contract import PointPx

EXAMPLE = Path(__file__).resolve().parents[1] / "config" / "calibration.example.json"


def test_load_calibration_example() -> None:
    settings = load_calibration_settings(EXAMPLE)
    assert settings.homography is not None
    assert len(settings.homography) == 3


def test_pixel_to_pickup_pose_with_homography() -> None:
    settings = CalibrationSettings(
        homography=(
            (0.25, 0.0, -80.0),
            (0.0, 0.25, -60.0),
            (0.0, 0.0, 1.0),
        )
    )
    center = PointPx(320.0, 240.0)
    pose = pixel_to_pickup_pose(center, 5.0, settings)
    assert pose is not None
    assert pose.theta_deg == 5.0


def test_pixel_to_pickup_pose_without_homography() -> None:
    assert pixel_to_pickup_pose(PointPx(1, 2), 0.0, CalibrationSettings()) is None

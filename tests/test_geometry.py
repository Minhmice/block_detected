"""GEO-03/04/05 geometry tests."""

from __future__ import annotations

import math

import cv2
import numpy as np
import pytest

from block_detected.detection_contract import CornersPx, PointPx
from block_detected.detector import DetectorSettings, SquareCandidate, find_square_candidates
from block_detected.geometry import (
    GeometrySettings,
    compute_center_and_angle,
    geometry_from_candidate,
    order_corners_tl_tr_br_bl,
    warp_face_bgr,
)
from block_detected.preprocess import PreprocessSettings, preprocess_bgr
from block_detected.vision import VisionSettings, find_square_candidates_from_frame
from block_detected.camera import CaptureFrame


def _rotated_quad_pts(center: tuple[int, int], half: float, angle_deg: float) -> np.ndarray:
    cx, cy = center
    corners = np.array(
        [[-half, -half], [half, -half], [half, half], [-half, half]],
        dtype=np.float64,
    )
    theta = math.radians(angle_deg)
    rot = np.array(
        [[math.cos(theta), -math.sin(theta)], [math.sin(theta), math.cos(theta)]],
    )
    return (corners @ rot.T) + np.array([cx, cy])


def test_order_corners_tl_tr_br_bl_axis_aligned() -> None:
    pts = np.array([[100, 50], [200, 50], [200, 150], [100, 150]], dtype=np.float64)
    corners = order_corners_tl_tr_br_bl(pts)
    assert corners.top_left == PointPx(100, 50)
    assert corners.top_right == PointPx(200, 50)
    assert corners.bottom_right == PointPx(200, 150)
    assert corners.bottom_left == PointPx(100, 150)


def test_order_corners_consistent_under_rotation() -> None:
    for angle in (0, 15, 45, 90, 135):
        pts = _rotated_quad_pts((320, 240), 70, angle)
        corners = order_corners_tl_tr_br_bl(pts)
        ordered = np.array(
            [
                [corners.top_left.x, corners.top_left.y],
                [corners.top_right.x, corners.top_right.y],
                [corners.bottom_right.x, corners.bottom_right.y],
                [corners.bottom_left.x, corners.bottom_left.y],
            ]
        )
        # Top edge should be above bottom edge (smaller y in image coords)
        assert corners.top_left.y < corners.bottom_left.y
        assert corners.top_right.y < corners.bottom_right.y
        assert corners.top_left.x < corners.top_right.x
        assert corners.bottom_left.x < corners.bottom_right.x
        warp = warp_face_bgr(
            np.zeros((480, 640, 3), dtype=np.uint8),
            corners,
            warp_size=128,
        )
        assert warp.shape == (128, 128, 3)


def test_center_and_angle_from_ordered_corners() -> None:
    corners = CornersPx(
        top_left=PointPx(100, 50),
        top_right=PointPx(200, 50),
        bottom_right=PointPx(200, 150),
        bottom_left=PointPx(100, 150),
    )
    center, angle = compute_center_and_angle(corners)
    assert center == PointPx(150, 100)
    assert abs(angle) < 1e-6


def test_geometry_from_candidate_on_synthetic_frame() -> None:
    frame = np.zeros((480, 640, 3), dtype=np.uint8)
    cv2.rectangle(frame, (260, 180), (380, 300), (235, 235, 235), -1)
    pre = preprocess_bgr(frame, PreprocessSettings())
    candidates = find_square_candidates(pre.mask, DetectorSettings())
    assert candidates
    geom = geometry_from_candidate(candidates[0], frame, GeometrySettings(warp_size=128))
    assert geom.warped_bgr.shape == (128, 128, 3)
    center, angle = compute_center_and_angle(geom.corners_px)
    assert geom.center_px == center
    assert abs(geom.angle_deg - angle) < 1e-6


def test_frame_pipeline_geometry_end_to_end() -> None:
    frame = np.zeros((480, 640, 3), dtype=np.uint8)
    cv2.rectangle(frame, (260, 180), (380, 300), (235, 235, 235), -1)
    capture = CaptureFrame(
        frame_id="frame_geom",
        image_bgr=frame,
        timestamp_ns=0,
        source="test",
    )
    found = find_square_candidates_from_frame(capture, VisionSettings())
    geom = geometry_from_candidate(found.candidates[0], frame)
    assert found.frame_id == "frame_geom"
    assert geom.warped_bgr.size > 0

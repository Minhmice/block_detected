"""GEO-02 contour detector tests."""

from __future__ import annotations

import json
from pathlib import Path

import cv2
import numpy as np
import pytest

from block_detected.detector import DetectorSettings, find_square_candidates
from block_detected.preprocess import PreprocessSettings, preprocess_bgr

REPO_ROOT = Path(__file__).resolve().parents[1]
VISION_EXAMPLE = REPO_ROOT / "config" / "vision.example.json"

DEFAULT_DETECTOR = DetectorSettings()


def _blank_mask() -> np.ndarray:
    return np.zeros((480, 640), dtype=np.uint8)


def _filled_square_mask(
    center: tuple[int, int] = (320, 240),
    half_side: int = 60,
) -> np.ndarray:
    mask = np.zeros((480, 640), dtype=np.uint8)
    cx, cy = center
    cv2.rectangle(
        mask,
        (cx - half_side, cy - half_side),
        (cx + half_side, cy + half_side),
        255,
        thickness=-1,
    )
    return mask


def _filled_rectangle_mask(width: int, height: int) -> np.ndarray:
    mask = np.zeros((480, 640), dtype=np.uint8)
    x0 = (640 - width) // 2
    y0 = (480 - height) // 2
    cv2.rectangle(mask, (x0, y0), (x0 + width, y0 + height), 255, thickness=-1)
    return mask


def _rotated_square_mask(center: tuple[int, int], side: int, angle_deg: float) -> np.ndarray:
    mask = np.zeros((480, 640), dtype=np.uint8)
    cx, cy = center
    half = side / 2.0
    pts = np.array(
        [
            [-half, -half],
            [half, -half],
            [half, half],
            [-half, half],
        ],
        dtype=np.float32,
    )
    theta = np.deg2rad(angle_deg)
    rot = np.array(
        [[np.cos(theta), -np.sin(theta)], [np.sin(theta), np.cos(theta)]],
        dtype=np.float32,
    )
    pts = (pts @ rot.T) + np.array([cx, cy], dtype=np.float32)
    cv2.fillPoly(mask, [pts.astype(np.int32)], 255)
    return mask


def test_square_candidate_filters_area_aspect_and_convexity() -> None:
    square = find_square_candidates(_filled_square_mask(half_side=60), DEFAULT_DETECTOR)
    assert len(square) >= 1

    wide = find_square_candidates(_filled_rectangle_mask(200, 60), DEFAULT_DETECTOR)
    assert len(wide) == 0

    tiny = find_square_candidates(_filled_square_mask(half_side=1), DEFAULT_DETECTOR)
    assert len(tiny) == 0


def test_empty_mask_returns_no_candidates() -> None:
    assert find_square_candidates(_blank_mask(), DEFAULT_DETECTOR) == []

    noise = np.zeros((480, 640), dtype=np.uint8)
    rng = np.random.default_rng(42)
    for _ in range(50):
        x, y = int(rng.integers(0, 640)), int(rng.integers(0, 480))
        noise[y, x] = 255
    assert find_square_candidates(noise, DEFAULT_DETECTOR) == []


def test_rotated_square_accepted_with_min_area_rect_aspect() -> None:
    mask = _rotated_square_mask((320, 240), 120, 45.0)
    candidates = find_square_candidates(mask, DEFAULT_DETECTOR)
    assert len(candidates) >= 1
    assert 0.75 <= candidates[0].aspect <= 1.33


def test_candidates_sorted_by_area_descending() -> None:
    mask = np.zeros((480, 640), dtype=np.uint8)
    cv2.rectangle(mask, (200, 180), (280, 260), 255, -1)
    cv2.rectangle(mask, (360, 200), (500, 340), 255, -1)
    candidates = find_square_candidates(mask, DEFAULT_DETECTOR)
    assert len(candidates) >= 2
    areas = [c.area_px for c in candidates]
    assert areas == sorted(areas, reverse=True)


def test_synthetic_visible_square_yields_candidate() -> None:
    mask = _filled_square_mask(half_side=60)
    assert len(find_square_candidates(mask, DEFAULT_DETECTOR)) >= 1


def test_preprocess_chain_yields_candidate() -> None:
    frame = np.zeros((480, 640, 3), dtype=np.uint8)
    cv2.rectangle(frame, (260, 180), (380, 300), (240, 240, 240), -1)
    pre = preprocess_bgr(frame, PreprocessSettings())
    candidates = find_square_candidates(pre.mask, DEFAULT_DETECTOR)
    assert len(candidates) >= 1


def test_vision_example_json_matches_detector_settings() -> None:
    data = json.loads(VISION_EXAMPLE.read_text(encoding="utf-8"))
    det = data["detector"]
    settings = DetectorSettings(
        min_area_px=det["min_area_px"],
        max_area_px=det["max_area_px"],
        aspect_min=det["aspect_min"],
        aspect_max=det["aspect_max"],
        approx_epsilon_ratio=det["approx_epsilon_ratio"],
    )
    assert settings.min_area_px == 1000

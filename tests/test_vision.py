"""Phase 3 integration: frame helper, fixture, overlay."""

from __future__ import annotations

import time
from pathlib import Path

import cv2
import numpy as np
import pytest

from block_detected.camera import CaptureFrame
from block_detected.vision import (
    VisionSettings,
    draw_candidate_overlay,
    find_square_candidates_from_frame,
)

FIXTURE_DIR = Path(__file__).resolve().parent / "fixtures" / "vision"
SQUARE_FACE_PATH = FIXTURE_DIR / "square_face.png"


def _default_settings() -> VisionSettings:
    return VisionSettings()


@pytest.fixture(scope="module", autouse=True)
def _ensure_square_face_fixture() -> None:
    if SQUARE_FACE_PATH.exists():
        return
    FIXTURE_DIR.mkdir(parents=True, exist_ok=True)
    frame = np.zeros((480, 640, 3), dtype=np.uint8)
    cv2.rectangle(frame, (260, 180), (380, 300), (235, 235, 235), -1)
    cv2.imwrite(str(SQUARE_FACE_PATH), frame)


def test_frame_helper_preserves_frame_id_and_finds_candidate() -> None:
    image = cv2.imread(str(SQUARE_FACE_PATH))
    assert image is not None
    assert image.shape == (480, 640, 3)

    capture = CaptureFrame(
        frame_id="frame_000099",
        image_bgr=image,
        timestamp_ns=time.time_ns(),
        source="fixture",
    )
    result = find_square_candidates_from_frame(capture, _default_settings())
    assert result.frame_id == "frame_000099"
    assert len(result.candidates) >= 1


def test_frame_helper_rejects_wrong_shape() -> None:
    capture = CaptureFrame(
        frame_id="frame_bad",
        image_bgr=np.zeros((240, 320, 3), dtype=np.uint8),
        timestamp_ns=0,
        source="test",
    )
    with pytest.raises(ValueError, match="expected"):
        find_square_candidates_from_frame(capture, _default_settings())


def test_overlay_does_not_mutate_source() -> None:
    frame = cv2.imread(str(SQUARE_FACE_PATH))
    assert frame is not None
    before = frame.copy()
    capture = CaptureFrame(
        frame_id="frame_overlay",
        image_bgr=frame,
        timestamp_ns=0,
        source="fixture",
    )
    result = find_square_candidates_from_frame(capture, _default_settings())
    _ = draw_candidate_overlay(frame, result.candidates)
    assert np.array_equal(frame, before)


def test_overlay_draws_when_candidates_present() -> None:
    frame = cv2.imread(str(SQUARE_FACE_PATH))
    assert frame is not None
    capture = CaptureFrame(
        frame_id="frame_draw",
        image_bgr=frame.copy(),
        timestamp_ns=0,
        source="fixture",
    )
    result = find_square_candidates_from_frame(capture, _default_settings())
    overlay = draw_candidate_overlay(frame, result.candidates)
    assert overlay.shape == frame.shape
    assert not np.array_equal(overlay, frame)

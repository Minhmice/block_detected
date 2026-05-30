"""Pytest fixtures for camera and debug tests."""

from __future__ import annotations

from pathlib import Path

import cv2
import numpy as np
import pytest


@pytest.fixture
def fixture_image_dir(tmp_path: Path) -> Path:
    """Single 640×480 BGR PNG for ImageSequenceFrameSource tests."""
    frames_dir = tmp_path / "frames"
    frames_dir.mkdir()
    image = np.zeros((480, 640, 3), dtype=np.uint8)
    image[:, :, 1] = 128
    path = frames_dir / "frame.png"
    cv2.imwrite(str(path), image)
    return frames_dir

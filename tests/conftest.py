"""Pytest fixtures for camera and debug tests."""

from __future__ import annotations

import sys
from pathlib import Path

import cv2
import numpy as np
import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "backend"))
sys.path.insert(0, str(ROOT / "src"))


def _hw_camera_available() -> bool:
    cap = cv2.VideoCapture(0)
    ok = cap.isOpened()
    cap.release()
    return ok


def pytest_configure(config: pytest.Config) -> None:
    config.addinivalue_line(
        "markers",
        "hw_camera: requires physical camera (skipped in CI)",
    )


hw_camera = pytest.mark.skipif(
    not _hw_camera_available(),
    reason="no physical camera attached",
)


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


@pytest.fixture(autouse=True)
def reset_camera_runtime():
    """Isolate API tests — runtime mock flag must not leak between tests."""
    try:
        from app.services.camera_runtime import camera_runtime

        camera_runtime.reset_for_tests()
    except ImportError:
        pass
    yield
    try:
        from app.services.camera_runtime import camera_runtime

        camera_runtime.reset_for_tests()
    except ImportError:
        pass

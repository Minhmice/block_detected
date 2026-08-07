"""USB camera open, scan, and switch (platform-aware OpenCV backend)."""

from __future__ import annotations

import logging
import sys

import cv2

logger = logging.getLogger(__name__)


def _video_backend() -> int:
    if sys.platform == "darwin":
        return cv2.CAP_AVFOUNDATION
    if sys.platform == "win32":
        return cv2.CAP_DSHOW
    return cv2.CAP_V4L2


def _open_capture(index: int) -> cv2.VideoCapture:
    backend = _video_backend()
    cap = cv2.VideoCapture(index, backend)
    if cap.isOpened():
        return cap
    if backend != 0:
        cap = cv2.VideoCapture(index)
    return cap


def open_v4l2(index: int, *, width: int, height: int) -> cv2.VideoCapture | None:
    cap = _open_capture(index)
    if not cap.isOpened():
        return None
    cap.set(cv2.CAP_PROP_FRAME_WIDTH, width)
    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, height)
    return cap


def try_open_index(index: int, *, width: int, height: int) -> cv2.VideoCapture | None:
    """Open index and verify frames can be read."""
    cap = open_v4l2(index, width=width, height=height)
    if cap is None:
        return None
    for _ in range(4):
        cap.read()
    ok, frame = cap.read()
    if ok and frame is not None and frame.size > 0:
        return cap
    cap.release()
    return None


def find_usb_camera(
    *,
    width: int,
    height: int,
    start_index: int = 0,
    max_index: int = 10,
) -> tuple[cv2.VideoCapture | None, int]:
    """Scan camera indices for a device that returns frames."""
    for idx in range(start_index, max_index + 1):
        cap = try_open_index(idx, width=width, height=height)
        if cap is not None:
            label = f"/dev/video{idx}" if sys.platform.startswith("linux") else f"index {idx}"
            logger.info("Found camera at %s", label)
            return cap, idx
    return None, -1


def switch_camera(
    cap: cv2.VideoCapture,
    current_camera: int,
    *,
    max_index: int,
    width: int,
    height: int,
) -> tuple[cv2.VideoCapture, int, bool]:
    if max_index < 0:
        return cap, current_camera, False

    next_camera = (current_camera + 1) % (max_index + 1)
    for _ in range(max_index + 1):
        if next_camera == current_camera:
            next_camera = (next_camera + 1) % (max_index + 1)
            continue
        new_cap = try_open_index(next_camera, width=width, height=height)
        if new_cap is not None:
            cap.release()
            return new_cap, next_camera, True
        next_camera = (next_camera + 1) % (max_index + 1)
    return cap, current_camera, False

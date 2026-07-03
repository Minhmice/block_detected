"""USB/V4L2 camera open and switch."""

from __future__ import annotations

import logging

import cv2

logger = logging.getLogger(__name__)


def open_v4l2(index: int, *, width: int, height: int) -> cv2.VideoCapture | None:
    cap = cv2.VideoCapture(index, cv2.CAP_V4L2)
    if not cap.isOpened():
        return None
    cap.set(cv2.CAP_PROP_FRAME_WIDTH, width)
    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, height)
    return cap


def find_usb_camera(
    *,
    width: int,
    height: int,
    start_index: int = 0,
    max_index: int = 10,
) -> tuple[cv2.VideoCapture | None, int]:
    """Scan V4L2 indices for a working USB camera."""
    for idx in range(start_index, max_index + 1):
        cap = cv2.VideoCapture(idx, cv2.CAP_V4L2)
        if not cap.isOpened():
            continue
        cap.set(cv2.CAP_PROP_FRAME_WIDTH, width)
        cap.set(cv2.CAP_PROP_FRAME_HEIGHT, height)
        for _ in range(4):
            cap.read()
        ok, frame = cap.read()
        if ok and frame is not None and frame.size > 0:
            logger.info("Found USB camera at /dev/video%s", idx)
            return cap, idx
        cap.release()
    return None, -1


def switch_camera(
    cap: cv2.VideoCapture,
    current_camera: int,
    *,
    max_index: int,
    width: int,
    height: int,
) -> tuple[cv2.VideoCapture, int, bool]:
    next_camera = (current_camera + 1) % (max_index + 1)
    for _ in range(max_index + 1):
        new_cap = open_v4l2(next_camera, width=width, height=height)
        if new_cap is not None:
            cap.release()
            return new_cap, next_camera, True
        next_camera = (next_camera + 1) % (max_index + 1)
    return cap, current_camera, False

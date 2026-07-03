"""Open camera by source type."""

from __future__ import annotations

import cv2

from block_detected.io.camera.pi.picamera2 import PiCameraCapture, open_libcamera
from block_detected.io.camera.pi.rpicam import RpicamCapture, open_rpicam
from block_detected.io.camera.v4l2 import open_v4l2


def open_camera(
    source: int | str,
    *,
    width: int,
    height: int,
) -> cv2.VideoCapture | PiCameraCapture | RpicamCapture | None:
    if isinstance(source, str) and source == "libcamera":
        return open_libcamera(width=width, height=height)
    if isinstance(source, str) and source == "rpicam":
        return open_rpicam(width=width, height=height)
    return open_v4l2(int(source), width=width, height=height)

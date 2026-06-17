"""Webcam capture and source switching."""

import logging

import cv2

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------


def _open_v4l2(index: int, *, width: int, height: int) -> cv2.VideoCapture | None:
    """Open a V4L2 (USB) camera by numeric index."""
    cap = cv2.VideoCapture(index)
    if not cap.isOpened():
        return None
    cap.set(cv2.CAP_PROP_FRAME_WIDTH, width)
    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, height)
    return cap


def _open_libcamera(*, width: int, height: int) -> cv2.VideoCapture | None:
    """Open Pi Camera Module via libcamera GStreamer pipeline.

    Requires OpenCV built with GStreamer support (``cv2.CAP_GSTREAMER``).
    """
    pipeline = (
        f"libcamerasrc ! "
        f"video/x-raw,width={width},height={height},framerate=30/1 ! "
        f"videoconvert ! videoscale ! appsink"
    )
    cap = cv2.VideoCapture(pipeline, cv2.CAP_GSTREAMER)
    if cap.isOpened():
        logger.info("Opened Pi Camera Module via libcamera GStreamer")
        return cap
    logger.warning("libcamera GStreamer pipeline failed — falling back to V4L2")
    cap.release()
    return None


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------


def open_camera(
    source: int | str,
    *,
    width: int,
    height: int,
) -> cv2.VideoCapture | None:
    """Open a camera source.

    Parameters
    ----------
    source : int | str
        Numeric V4L2 index (e.g. ``0`` for USB webcam) or the string ``"libcamera"``
        for Raspberry Pi Camera Module (libcamera GStreamer pipeline).
    """
    if isinstance(source, str) and source == "libcamera":
        return _open_libcamera(width=width, height=height)
    return _open_v4l2(int(source), width=width, height=height)


def switch_camera(
    cap: cv2.VideoCapture,
    current_camera: int,
    *,
    max_index: int,
    width: int,
    height: int,
) -> tuple[cv2.VideoCapture, int, bool]:
    """Try the next available camera index. Returns ``(cap, new_index, switched)``."""
    next_camera = (current_camera + 1) % (max_index + 1)

    for _ in range(max_index + 1):
        new_cap = _open_v4l2(next_camera, width=width, height=height)
        if new_cap is not None:
            cap.release()
            return new_cap, next_camera, True
        next_camera = (next_camera + 1) % (max_index + 1)

    return cap, current_camera, False

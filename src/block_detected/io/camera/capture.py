"""Webcam capture and source switching.

Pi Camera Module uses ``picamera2`` (official Pi 5 / Bookworm API).
USB webcams use V4L2 with warm-up reads.
"""

from __future__ import annotations

import logging
import time
from typing import Any

import cv2

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Pi Camera Module wrapper (picamera2 → duck-types cv2.VideoCapture)
# ---------------------------------------------------------------------------

class PiCameraCapture:
    """Minimal ``cv2.VideoCapture``-compatible wrapper around ``picamera2``."""

    def __init__(self, *, width: int, height: int) -> None:
        from picamera2 import Picamera2  # lazy import – only on Pi

        self._width = width
        self._height = height
        self._picam2 = Picamera2()
        config = self._picam2.create_preview_configuration(
            main={"size": (width, height), "format": "RGB888"},
        )
        self._picam2.configure(config)
        self._picam2.start()
        time.sleep(0.5)  # let AE/AWB settle

    def read(self) -> tuple[bool, Any]:
        frame = self._picam2.capture_array("main")
        return True, frame

    def isOpened(self) -> bool:
        return True

    def release(self) -> None:
        try:
            self._picam2.stop()
            self._picam2.close()
        except Exception:
            pass

    def set(self, _prop: int, _value: float) -> bool:
        return True  # no-op – picamera2 handles this in configure

    def getBackendName(self) -> str:
        return "picamera2"


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------


def _open_v4l2(index: int, *, width: int, height: int) -> cv2.VideoCapture | None:
    """Open a V4L2 camera by numeric index."""
    cap = cv2.VideoCapture(index, cv2.CAP_V4L2)
    if not cap.isOpened():
        return None
    cap.set(cv2.CAP_PROP_FRAME_WIDTH, width)
    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, height)
    return cap


def _open_gstreamer(*, width: int, height: int) -> cv2.VideoCapture | None:
    """Open Pi Camera Module directly via GStreamer + libcamerasrc.

    Bypasses ``picamera2`` entirely — works on Python 3.13+ as long as
    OpenCV was built with GStreamer support and ``libcamera`` is installed.
    """
    pipeline = (
        "libcamerasrc ! "
        f"video/x-raw,width={width},height={height},framerate=30/1 ! "
        "videoconvert ! appsink"
    )
    try:
        cap = cv2.VideoCapture(pipeline, cv2.CAP_GSTREAMER)
    except Exception:
        logger.debug("cv2.CAP_GSTREAMER not available (no GStreamer support in OpenCV)")
        return None
    if cap.isOpened():
        logger.info("Opened Pi Camera Module via GStreamer (libcamerasrc)")
        return cap
    logger.warning("GStreamer pipeline failed")
    cap.release()
    return None


def _open_libcamera(*, width: int, height: int) -> cv2.VideoCapture | PiCameraCapture | None:
    """Open Pi Camera Module via picamera2, with GStreamer fallback.

    Returns a ``PiCameraCapture`` duck-typing ``cv2.VideoCapture``,
    or *None* if picamera2 / GStreamer are not available.
    """
    try:
        cap = PiCameraCapture(width=width, height=height)
        logger.info("Opened Pi Camera Module via picamera2")
        return cap
    except Exception as exc:
        logger.warning("picamera2 failed: %s", exc)

    return _open_gstreamer(width=width, height=height)


def _find_usb_camera(
    *,
    width: int,
    height: int,
    start_index: int = 0,
    max_index: int = 10,
) -> tuple[cv2.VideoCapture | None, int]:
    """Scan V4L2 indices for a working USB camera.

    Uses ``cv2.CAP_V4L2`` backend and runs warm-up reads so the camera
    is ready for the inference loop.  On Pi with ``bcm2835-v4l2`` loaded
    the Pi Camera Module appears as a regular V4L2 device too.

    Returns ``(cap, index)`` or ``(None, -1)``.
    """
    for idx in range(start_index, max_index + 1):
        cap = cv2.VideoCapture(idx, cv2.CAP_V4L2)
        if not cap.isOpened():
            continue
        cap.set(cv2.CAP_PROP_FRAME_WIDTH, width)
        cap.set(cv2.CAP_PROP_FRAME_HEIGHT, height)
        # Warm-up: discard first few frames so set() takes effect
        for _ in range(4):
            cap.read()
        ok, frame = cap.read()
        if ok and frame is not None and frame.size > 0:
            logger.info("Found USB camera at /dev/video%s", idx)
            return cap, idx
        cap.release()
    return None, -1


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def find_usb_camera(
    *,
    width: int,
    height: int,
    start_index: int = 0,
    max_index: int = 10,
) -> tuple[cv2.VideoCapture | PiCameraCapture | None, int]:
    """Public wrapper — scan for a working USB V4L2 camera on the system."""
    return _find_usb_camera(
        width=width, height=height,
        start_index=start_index, max_index=max_index,
    )


def open_camera(
    source: int | str,
    *,
    width: int,
    height: int,
) -> cv2.VideoCapture | PiCameraCapture | None:
    """Open a camera source.

    Parameters
    ----------
    source : int | str
        Numeric V4L2 index (e.g. ``0``) or ``"libcamera"`` for Pi Camera Module.
    """
    if isinstance(source, str) and source == "libcamera":
        return _open_libcamera(width=width, height=height)
    if isinstance(source, str) and source == "gstreamer":
        return _open_gstreamer(width=width, height=height)
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

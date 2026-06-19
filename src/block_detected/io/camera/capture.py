"""Webcam capture and source switching.

USB webcams use V4L2 with warm-up reads.
Pi Camera Module uses ``rpicam-vid`` subprocess (YUV420 → BGR).
"""

from __future__ import annotations

import logging
import subprocess
import threading
import time
from typing import Any

import cv2
import numpy as np

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Pi Camera Module wrapper (rpicam-vid background thread → duck-types)
# ---------------------------------------------------------------------------


class RpicamCapture:
    """``cv2.VideoCapture``-compatible wrapper around ``rpicam-vid``.

    A background thread continuously reads raw YUV420 frames from
    ``rpicam-vid`` stdout, converts to BGR, and keeps the latest frame.
    ``read()`` returns instantly — no blocking on I/O.
    """

    def __init__(self, *, width: int, height: int) -> None:
        self._width = width
        self._height = height
        self._frame_bytes = width * height * 3 // 2
        self._proc = subprocess.Popen(
            [
                "rpicam-vid",
                "-t", "0",
                "--width", str(width),
                "--height", str(height),
                "--codec", "yuv420",
                "--output", "-",
                "--inline",
            ],
            stdout=subprocess.PIPE,
            stderr=subprocess.DEVNULL,
            bufsize=10 ** 8,
        )
        self._latest: Any = None          # latest BGR frame
        self._lock = threading.Lock()
        self._running = True
        self._thread = threading.Thread(target=self._reader_loop, daemon=True)
        self._thread.start()
        # Let AE/AWB settle
        time.sleep(0.5)

    def _reader_loop(self) -> None:
        """Background thread: read YUV420 → BGR, keep latest."""
        assert self._proc.stdout is not None
        while self._running:
            raw = self._proc.stdout.read(self._frame_bytes)
            if raw is None or len(raw) != self._frame_bytes:
                # Subprocess may have died — stop
                self._running = False
                break
            yuv = np.frombuffer(raw, dtype=np.uint8).reshape(
                (self._height * 3 // 2, self._width)
            )
            bgr = cv2.cvtColor(yuv, cv2.COLOR_YUV2BGR_I420)
            with self._lock:
                self._latest = bgr

    def read(self) -> tuple[bool, Any]:
        with self._lock:
            if self._latest is None:
                return False, None
            frame = self._latest.copy()
        return True, frame

    def isOpened(self) -> bool:
        return self._running and self._proc is not None and self._proc.poll() is None

    def release(self) -> None:
        self._running = False
        if self._proc is not None:
            self._proc.terminate()
            try:
                self._proc.wait(timeout=2)
            except subprocess.TimeoutExpired:
                self._proc.kill()
            self._proc = None
        if self._thread.is_alive():
            self._thread.join(timeout=1)

    def set(self, _prop: int, _value: float) -> bool:
        return True

    def getBackendName(self) -> str:
        return "rpicam-vid"

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


def _open_rpicam(*, width: int, height: int) -> RpicamCapture | None:
    """Open Pi Camera Module via ``rpicam-vid`` subprocess (YUV420 → BGR).

    No Python libcamera/picamera2 bindings required — works on any
    Python version as long as ``rpicam-vid`` is installed on the system.
    """
    try:
        cap = RpicamCapture(width=width, height=height)
        logger.info("Opened Pi Camera Module via rpicam-vid (%sx%s)", width, height)
        return cap
    except Exception as exc:
        logger.warning("rpicam-vid failed: %s", exc)
        return None


def _open_libcamera(*, width: int, height: int) -> cv2.VideoCapture | PiCameraCapture | None:
    """Open Pi Camera Module via picamera2, with rpicam-vid fallback."""
    try:
        cap = PiCameraCapture(width=width, height=height)
        logger.info("Opened Pi Camera Module via picamera2")
        return cap
    except Exception as exc:
        logger.warning("picamera2 failed: %s", exc)

    return _open_rpicam(width=width, height=height)


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
) -> tuple[cv2.VideoCapture | PiCameraCapture | RpicamCapture | None, int]:
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
) -> cv2.VideoCapture | PiCameraCapture | RpicamCapture | None:
    """Open a camera source.

    Parameters
    ----------
    source : int | str
        Numeric V4L2 index (e.g. ``0``), ``"libcamera"`` for Pi Camera Module
        (picamera2), or ``"rpicam"`` for Pi Camera via ``rpicam-vid`` subprocess.
    """
    if isinstance(source, str) and source == "libcamera":
        return _open_libcamera(width=width, height=height)
    if isinstance(source, str) and source == "rpicam":
        return _open_rpicam(width=width, height=height)
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

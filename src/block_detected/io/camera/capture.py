"""Webcam capture and source switching."""

import logging

import cv2

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------


def _open_v4l2(index: int, *, width: int, height: int) -> cv2.VideoCapture | None:
    """Open a V4L2 camera by numeric index."""
    cap = cv2.VideoCapture(index)
    if not cap.isOpened():
        return None
    cap.set(cv2.CAP_PROP_FRAME_WIDTH, width)
    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, height)
    return cap


def _open_libcamera(*, width: int, height: int) -> cv2.VideoCapture | None:
    """Open Pi Camera Module.

    On Pi 5 / Bookworm the CSI camera appears as a V4L2 device (/dev/video0).
    We try V4L2 first; fall back to GStreamer for older setups.
    """
    # Pi 5 Bookworm: Pi Camera via V4L2 (always available)
    cap = _open_v4l2(0, width=width, height=height)
    if cap is not None:
        logger.info("Opened Pi Camera Module via V4L2 (/dev/video0)")
        return cap

    # Fallback: GStreamer pipeline (older Pi OS or custom OpenCV build)
    pipeline = (
        f"libcamerasrc ! "
        f"video/x-raw,width={width},height={height},framerate=30/1 ! "
        f"videoconvert ! videoscale ! appsink"
    )
    try:
        cap = cv2.VideoCapture(pipeline, cv2.CAP_GSTREAMER)
    except Exception:
        logger.debug("cv2.CAP_GSTREAMER not available (no GStreamer support in OpenCV)")
        return None
    if cap.isOpened():
        logger.info("Opened Pi Camera Module via libcamera GStreamer")
        return cap
    logger.warning("libcamera GStreamer pipeline failed")
    cap.release()
    return None


def _find_usb_camera(
    *,
    width: int,
    height: int,
    start_index: int = 1,
    max_index: int = 8,
) -> tuple[cv2.VideoCapture | None, int]:
    """Scan V4L2 indices starting from *start_index* for a working USB camera.

    On Raspberry Pi /dev/video0 is typically the CSI camera, so we skip it.
    Returns ``(cap, index)`` or ``(None, -1)``.
    """
    for idx in range(start_index, max_index + 1):
        cap = _open_v4l2(idx, width=width, height=height)
        if cap is None:
            continue
        ok, _ = cap.read()
        if ok:
            logger.info("Found USB camera at /dev/video%s", idx)
            return cap, idx
        cap.release()
    return None, -1


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def find_usb_camera(*, width: int, height: int, max_index: int = 8) -> tuple[cv2.VideoCapture | None, int]:
    """Public wrapper — scan for a working USB V4L2 camera on the system."""
    return _find_usb_camera(width=width, height=height, max_index=max_index)


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

"""Pi Camera Module via picamera2."""

from __future__ import annotations

import time
from typing import Any

from block_detected.io.camera.pi.rpicam import RpicamCapture, open_rpicam


class PiCameraCapture:
    """Minimal ``cv2.VideoCapture``-compatible wrapper around ``picamera2``."""

    def __init__(self, *, width: int, height: int) -> None:
        from picamera2 import Picamera2

        self._width = width
        self._height = height
        self._picam2 = Picamera2()
        config = self._picam2.create_preview_configuration(
            main={"size": (width, height), "format": "RGB888"},
        )
        self._picam2.configure(config)
        self._picam2.start()
        time.sleep(0.5)

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
        return True

    def getBackendName(self) -> str:
        return "picamera2"


def open_libcamera(*, width: int, height: int) -> PiCameraCapture | RpicamCapture | None:
    import logging

    logger = logging.getLogger(__name__)
    try:
        cap = PiCameraCapture(width=width, height=height)
        logger.info("Opened Pi Camera Module via picamera2")
        return cap
    except Exception as exc:
        logger.warning("picamera2 failed: %s", exc)
    return open_rpicam(width=width, height=height)

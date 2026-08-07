"""Pi Camera Module via rpicam-vid subprocess."""

from __future__ import annotations

import logging
import subprocess
import threading
import time
from typing import Any

import cv2
import numpy as np

logger = logging.getLogger(__name__)


class RpicamCapture:
    """``cv2.VideoCapture``-compatible wrapper around ``rpicam-vid``."""

    def __init__(self, *, width: int, height: int) -> None:
        self._width = width
        self._height = height
        self._frame_bytes = width * height * 3 // 2
        self._proc = subprocess.Popen(
            [
                "rpicam-vid",
                "-t",
                "0",
                "--width",
                str(width),
                "--height",
                str(height),
                "--codec",
                "yuv420",
                "--output",
                "-",
                "--inline",
            ],
            stdout=subprocess.PIPE,
            stderr=subprocess.DEVNULL,
            bufsize=10**8,
        )
        self._latest: Any = None
        self._lock = threading.Lock()
        self._running = True
        self._thread = threading.Thread(target=self._reader_loop, daemon=True)
        self._thread.start()
        time.sleep(0.5)

    def _reader_loop(self) -> None:
        assert self._proc.stdout is not None
        while self._running:
            raw = self._proc.stdout.read(self._frame_bytes)
            if raw is None or len(raw) != self._frame_bytes:
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
            return True, self._latest.copy()

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


def open_rpicam(*, width: int, height: int) -> RpicamCapture | None:
    try:
        cap = RpicamCapture(width=width, height=height)
        logger.info("Opened Pi Camera Module via rpicam-vid (%sx%s)", width, height)
        return cap
    except Exception as exc:
        logger.warning("rpicam-vid failed: %s", exc)
        return None

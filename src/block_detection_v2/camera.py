from __future__ import annotations

import cv2

from . import config


class Camera:
    def __init__(self, index: int | None = None, width: int | None = None, height: int | None = None):
        self._index = config.CAMERA_INDEX if index is None else index
        self._width = config.FRAME_WIDTH if width is None else width
        self._height = config.FRAME_HEIGHT if height is None else height
        self._cap: cv2.VideoCapture | None = None

    def open(self) -> bool:
        self._cap = cv2.VideoCapture(self._index)
        if not self._cap.isOpened():
            return False
        self._cap.set(cv2.CAP_PROP_FRAME_WIDTH, self._width)
        self._cap.set(cv2.CAP_PROP_FRAME_HEIGHT, self._height)
        return True

    def read(self):
        if self._cap is None:
            return False, None
        return self._cap.read()

    def release(self) -> None:
        if self._cap is not None:
            self._cap.release()
            self._cap = None

from __future__ import annotations

import re
from pathlib import Path
from typing import List

import cv2

from . import config

_IMAGE_EXTS = {".jpg", ".jpeg", ".png", ".bmp", ".webp"}

KEY_ESC = 27
KEY_LEFT = {65361, 2, 81, ord("p"), ord("P")}
KEY_RIGHT = {65363, 3, 83, ord("n"), ord("N"), ord(" ")}


def _natural_sort_key(path: Path):
    parts = re.split(r"(\d+)", path.name)
    return [int(x) if x.isdigit() else x.lower() for x in parts]


class ImageFolder:
    def __init__(self, folder: str | None = None):
        self._folder = Path(folder or config.IMAGE_DIR)
        self._paths: List[Path] = []
        self._index = 0

    def open(self) -> bool:
        if not self._folder.is_dir():
            return False
        self._paths = sorted(
            (p for p in self._folder.iterdir() if p.is_file() and p.suffix.lower() in _IMAGE_EXTS),
            key=_natural_sort_key,
        )
        self._index = 0
        return len(self._paths) > 0

    def count(self) -> int:
        return len(self._paths)

    def index(self) -> int:
        return self._index + 1 if self._paths else 0

    def current_name(self) -> str:
        if not self._paths:
            return ""
        return self._paths[self._index].name

    def read(self):
        if not self._paths:
            return False, None
        frame = cv2.imread(str(self._paths[self._index]))
        if frame is None:
            return False, None
        return True, frame

    def next_image(self) -> bool:
        if not self._paths:
            return False
        self._index = (self._index + 1) % len(self._paths)
        return True

    def prev_image(self) -> bool:
        if not self._paths:
            return False
        self._index = (self._index - 1) % len(self._paths)
        return True

    def release(self) -> None:
        self._paths = []
        self._index = 0


def open_image_source(folder: str | None = None) -> ImageFolder:
    src = ImageFolder(folder)
    if not src.open():
        path = folder or config.IMAGE_DIR
        raise SystemExit(f"no images in {path}")
    return src


def navigation_hint(src: ImageFolder) -> str:
    return f"[{src.index()}/{src.count()}] {src.current_name()}  <- -> prev/next  ESC quit"


def is_prev_key(key: int) -> bool:
    return key in KEY_LEFT


def is_next_key(key: int) -> bool:
    return key in KEY_RIGHT


def wait_key(delay_ms: int) -> int:
    if hasattr(cv2, "waitKeyEx"):
        return cv2.waitKeyEx(max(delay_ms, 1))
    return cv2.waitKey(max(delay_ms, 1))

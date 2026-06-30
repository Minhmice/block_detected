from __future__ import annotations

import cv2
import numpy as np

from . import config


def preprocess(frame: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
    work = frame
    if config.RESIZE_WIDTH and config.RESIZE_WIDTH > 0:
        h, w = frame.shape[:2]
        scale = config.RESIZE_WIDTH / float(w)
        work = cv2.resize(frame, (config.RESIZE_WIDTH, int(h * scale)))

    gray = cv2.cvtColor(work, cv2.COLOR_BGR2GRAY)
    clahe = cv2.createCLAHE(clipLimit=config.CLAHE_CLIP, tileGridSize=config.CLAHE_TILE)
    gray = clahe.apply(gray)
    blurred = cv2.GaussianBlur(gray, config.GAUSSIAN_KERNEL, 0)
    return work, blurred

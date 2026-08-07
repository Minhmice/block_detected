"""Frame preprocessing before YOLO inference."""

from __future__ import annotations

from typing import Any

import cv2
import numpy as np


def apply_preprocess(
    frame: Any,
    *,
    contrast: float,
    brightness: int,
    saturation: float,
    blur_kernel: int,
) -> Any:
    """Apply contrast/brightness/saturation and optional Gaussian blur."""
    if frame is None:
        return frame

    alpha = float(contrast)
    beta = float(brightness)
    if alpha != 1.0 or beta != 0:
        frame = cv2.convertScaleAbs(frame, alpha=alpha, beta=beta)

    if saturation != 1.0:
        hsv = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV).astype(np.float32)
        hsv[:, :, 1] = np.clip(hsv[:, :, 1] * saturation, 0, 255)
        frame = cv2.cvtColor(hsv.astype(np.uint8), cv2.COLOR_HSV2BGR)

    if blur_kernel >= 3 and blur_kernel % 2 == 1:
        frame = cv2.GaussianBlur(frame, (blur_kernel, blur_kernel), 0)

    return frame

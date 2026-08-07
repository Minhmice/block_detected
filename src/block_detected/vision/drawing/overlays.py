"""Optional classical CV overlays drawn on the annotated preview frame."""

from __future__ import annotations

from typing import Any

import cv2
import numpy as np


def draw_contours_overlay(
    frame: Any,
    *,
    blur_kernel: int,
    canny_low: int,
    canny_high: int,
) -> None:
    gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
    if blur_kernel >= 3 and blur_kernel % 2 == 1:
        gray = cv2.GaussianBlur(gray, (blur_kernel, blur_kernel), 0)
    edges = cv2.Canny(gray, canny_low, canny_high)
    contours, _ = cv2.findContours(edges, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    cv2.drawContours(frame, contours, -1, (76, 215, 246), 1)


def draw_corners_overlay(frame: Any, *, max_corners: int = 80) -> None:
    gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
    corners = cv2.goodFeaturesToTrack(
        gray,
        maxCorners=max_corners,
        qualityLevel=0.01,
        minDistance=8,
        blockSize=3,
    )
    if corners is None:
        return
    for point in corners.reshape(-1, 2):
        x, y = int(point[0]), int(point[1])
        cv2.circle(frame, (x, y), 3, (78, 222, 163), -1)

from __future__ import annotations

from typing import List, Tuple

import cv2
import numpy as np

from . import config

LineSegment = Tuple[Tuple[int, int], Tuple[int, int]]


def detect_edges(gray: np.ndarray) -> tuple[np.ndarray, List[LineSegment]]:
    edges = cv2.Canny(
        gray,
        config.CANNY_LOW,
        config.CANNY_HIGH,
        apertureSize=config.CANNY_APERTURE,
    )
    kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (3, 3))
    edges = cv2.morphologyEx(edges, cv2.MORPH_CLOSE, kernel)

    lines: List[LineSegment] = []
    if config.USE_LSD and hasattr(cv2, "createLineSegmentDetector"):
        lsd = cv2.createLineSegmentDetector(0)
        detected, _, _, _ = lsd.detect(gray)
        if detected is not None:
            for seg in detected:
                x1, y1, x2, y2 = seg[0]
                lines.append(((int(x1), int(y1)), (int(x2), int(y2))))
    else:
        raw = cv2.HoughLinesP(
            edges,
            config.HOUGH_RHO,
            np.deg2rad(config.HOUGH_THETA_DEG),
            config.HOUGH_THRESHOLD,
            minLineLength=config.HOUGH_MIN_LINE_LEN,
            maxLineGap=config.HOUGH_MAX_LINE_GAP,
        )
        if raw is not None:
            for item in raw:
                x1, y1, x2, y2 = item[0]
                lines.append(((int(x1), int(y1)), (int(x2), int(y2))))

    return edges, lines

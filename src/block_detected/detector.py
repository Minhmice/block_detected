"""GEO-02: square-face contour candidates from binary masks."""

from __future__ import annotations

from dataclasses import dataclass

import cv2
import numpy as np

from .camera import TARGET_HEIGHT, TARGET_WIDTH

MASK_SHAPE = (TARGET_HEIGHT, TARGET_WIDTH)


@dataclass(frozen=True)
class DetectorSettings:
    min_area_px: float = 1_000.0
    max_area_px: float = 80_000.0
    aspect_min: float = 0.75
    aspect_max: float = 1.33
    approx_epsilon_ratio: float = 0.03

    def __post_init__(self) -> None:
        if self.min_area_px < 0 or self.max_area_px <= self.min_area_px:
            raise ValueError("max_area_px must be greater than min_area_px")
        if self.aspect_min <= 0 or self.aspect_max < self.aspect_min:
            raise ValueError("invalid aspect bounds")
        if self.approx_epsilon_ratio <= 0:
            raise ValueError("approx_epsilon_ratio must be positive")


@dataclass(frozen=True)
class SquareCandidate:
    approx_xy: np.ndarray
    area_px: float
    aspect: float
    bbox_xywh: tuple[int, int, int, int]
    score: float

    def __post_init__(self) -> None:
        if self.approx_xy.shape != (4, 2):
            raise ValueError(f"approx_xy must be (4, 2); got {self.approx_xy.shape!r}")


def _validate_mask(mask: np.ndarray) -> None:
    if mask.ndim != 2:
        raise ValueError(f"mask must be 2D; got shape {mask.shape!r}")
    if mask.dtype != np.uint8:
        raise ValueError(f"mask must be uint8; got {mask.dtype!r}")
    if mask.shape != MASK_SHAPE:
        raise ValueError(f"mask expected shape {MASK_SHAPE}; got {mask.shape!r}")


def _aspect_from_min_area_rect(approx: np.ndarray) -> float:
    (_, _), (width, height), _ = cv2.minAreaRect(approx.astype(np.float32))
    short_side = max(1.0, min(float(width), float(height)))
    long_side = max(float(width), float(height))
    return long_side / short_side


def find_square_candidates(
    mask: np.ndarray,
    settings: DetectorSettings,
) -> list[SquareCandidate]:
    """Return convex 4-vertex quads within area and aspect bounds, sorted by score descending."""
    _validate_mask(mask)

    contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    candidates: list[SquareCandidate] = []

    for contour in contours:
        area = float(cv2.contourArea(contour))
        if area < settings.min_area_px or area > settings.max_area_px:
            continue

        perimeter = cv2.arcLength(contour, True)
        approx = cv2.approxPolyDP(contour, settings.approx_epsilon_ratio * perimeter, True)
        if len(approx) != 4:
            continue
        if not cv2.isContourConvex(approx):
            continue

        aspect = _aspect_from_min_area_rect(approx)
        if not (settings.aspect_min <= aspect <= settings.aspect_max):
            continue

        x, y, w, h = cv2.boundingRect(approx)
        approx_xy = approx.reshape(4, 2).astype(np.float64)
        candidates.append(
            SquareCandidate(
                approx_xy=approx_xy,
                area_px=area,
                aspect=aspect,
                bbox_xywh=(int(x), int(y), int(w), int(h)),
                score=area,
            )
        )

    return sorted(candidates, key=lambda c: c.score, reverse=True)

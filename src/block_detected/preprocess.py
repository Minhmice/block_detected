"""GEO-01: BGR preprocessing to binary masks for contour detection."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Literal

import cv2
import numpy as np

from .camera import TARGET_HEIGHT, TARGET_WIDTH

TARGET_SHAPE = (TARGET_HEIGHT, TARGET_WIDTH, 3)
MASK_SHAPE = (TARGET_HEIGHT, TARGET_WIDTH)

ThresholdTypeName = Literal["THRESH_BINARY", "THRESH_BINARY_INV"]
PreprocessMode = Literal["adaptive_threshold", "canny"]


def _validate_odd_kernel(kernel: tuple[int, int], name: str) -> None:
    for value in kernel:
        if value < 1 or value % 2 == 0:
            raise ValueError(f"{name} must be odd positive ints; got {kernel!r}")


def _threshold_type_from_name(name: ThresholdTypeName) -> int:
    if name == "THRESH_BINARY":
        return cv2.THRESH_BINARY
    if name == "THRESH_BINARY_INV":
        return cv2.THRESH_BINARY_INV
    raise ValueError(f"unsupported adaptive_threshold_type: {name!r}")


@dataclass(frozen=True)
class PreprocessSettings:
    mode: PreprocessMode = "adaptive_threshold"
    blur_kernel: tuple[int, int] = (5, 5)
    adaptive_block_size: int = 31
    adaptive_c: int = 5
    adaptive_threshold_type: ThresholdTypeName = "THRESH_BINARY_INV"
    canny_low: int = 50
    canny_high: int = 150
    morph_kernel: tuple[int, int] = (3, 3)
    morph_open_iterations: int = 1
    morph_close_iterations: int = 1

    def __post_init__(self) -> None:
        _validate_odd_kernel(self.blur_kernel, "blur_kernel")
        _validate_odd_kernel(self.morph_kernel, "morph_kernel")
        if self.adaptive_block_size < 3 or self.adaptive_block_size % 2 == 0:
            raise ValueError("adaptive_block_size must be odd and >= 3")
        if self.morph_open_iterations < 0 or self.morph_close_iterations < 0:
            raise ValueError("morph iterations must be non-negative")


@dataclass(frozen=True)
class PreprocessResult:
    gray: np.ndarray
    blurred: np.ndarray
    raw_mask: np.ndarray
    opened: np.ndarray
    mask: np.ndarray


def _validate_frame_bgr(frame_bgr: np.ndarray) -> None:
    if frame_bgr.ndim != 3 or frame_bgr.shape[2] != 3:
        raise ValueError(f"expected BGR image (H, W, 3); got shape {frame_bgr.shape!r}")
    if frame_bgr.dtype != np.uint8:
        raise ValueError(f"expected uint8 BGR; got dtype {frame_bgr.dtype!r}")
    if frame_bgr.shape != TARGET_SHAPE:
        raise ValueError(f"expected shape {TARGET_SHAPE}; got {frame_bgr.shape!r}")


def preprocess_bgr(frame_bgr: np.ndarray, settings: PreprocessSettings) -> PreprocessResult:
    """Convert 640×480 BGR to grayscale, blur, threshold/Canny, and morphology masks."""
    _validate_frame_bgr(frame_bgr)

    gray = cv2.cvtColor(frame_bgr, cv2.COLOR_BGR2GRAY)
    blurred = cv2.GaussianBlur(gray, settings.blur_kernel, 0)

    if settings.mode == "adaptive_threshold":
        raw_mask = cv2.adaptiveThreshold(
            blurred,
            255,
            cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
            _threshold_type_from_name(settings.adaptive_threshold_type),
            settings.adaptive_block_size,
            settings.adaptive_c,
        )
    elif settings.mode == "canny":
        raw_mask = cv2.Canny(blurred, settings.canny_low, settings.canny_high)
    else:
        raise ValueError(f"unsupported preprocess mode: {settings.mode!r}")

    kernel = cv2.getStructuringElement(cv2.MORPH_RECT, settings.morph_kernel)
    opened = cv2.morphologyEx(
        raw_mask,
        cv2.MORPH_OPEN,
        kernel,
        iterations=settings.morph_open_iterations,
    )
    mask = cv2.morphologyEx(
        opened,
        cv2.MORPH_CLOSE,
        kernel,
        iterations=settings.morph_close_iterations,
    )

    for name, arr in (
        ("gray", gray),
        ("blurred", blurred),
        ("raw_mask", raw_mask),
        ("opened", opened),
        ("mask", mask),
    ):
        if arr.shape != MASK_SHAPE or arr.dtype != np.uint8:
            raise RuntimeError(f"{name} expected {MASK_SHAPE} uint8; got {arr.shape} {arr.dtype}")

    return PreprocessResult(gray=gray, blurred=blurred, raw_mask=raw_mask, opened=opened, mask=mask)

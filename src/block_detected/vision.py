"""Frame-level vision: preprocess + contour candidates + debug overlay."""

from __future__ import annotations

from dataclasses import dataclass

import cv2
import numpy as np

from .camera import TARGET_SHAPE, CaptureFrame
from .detector import DetectorSettings, SquareCandidate, find_square_candidates
from .preprocess import PreprocessResult, PreprocessSettings, preprocess_bgr


@dataclass(frozen=True)
class VisionSettings:
    preprocess: PreprocessSettings = PreprocessSettings()
    detector: DetectorSettings = DetectorSettings()


@dataclass(frozen=True)
class FrameCandidates:
    frame_id: str
    candidates: list[SquareCandidate]
    preprocess: PreprocessResult


def _validate_capture_frame(capture: CaptureFrame) -> None:
    image = capture.image_bgr
    if image.shape != TARGET_SHAPE or image.dtype != np.uint8:
        raise ValueError(f"expected {TARGET_SHAPE} uint8 BGR; got {image.shape} {image.dtype!r}")


def find_square_candidates_from_frame(
    capture: CaptureFrame,
    settings: VisionSettings,
) -> FrameCandidates:
    """Run preprocess → detector; preserve frame_id for downstream debug."""
    _validate_capture_frame(capture)
    pre = preprocess_bgr(capture.image_bgr, settings.preprocess)
    candidates = find_square_candidates(pre.mask, settings.detector)
    return FrameCandidates(
        frame_id=capture.frame_id,
        candidates=candidates,
        preprocess=pre,
    )


def draw_candidate_overlay(
    frame_bgr: np.ndarray,
    candidates: list[SquareCandidate],
) -> np.ndarray:
    """Draw accepted quads on a copy of frame_bgr; source array is not modified."""
    overlay = frame_bgr.copy()
    for candidate in candidates:
        points = candidate.approx_xy.reshape(-1, 1, 2).astype(np.int32)
        cv2.drawContours(overlay, [points], -1, (0, 255, 0), 2)
        x, y, _, _ = candidate.bbox_xywh
        label = f"area={candidate.area_px:.0f} aspect={candidate.aspect:.2f}"
        cv2.putText(
            overlay,
            label,
            (x, max(0, y - 8)),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.45,
            (0, 255, 0),
            1,
            cv2.LINE_AA,
        )
    return overlay

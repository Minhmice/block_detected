"""Public detection entry point (Phase 1 skeleton — no vision processing)."""

from __future__ import annotations

from typing import Mapping, Optional

from .detection_contract import (
    DetectionResult,
    make_multiple_candidates_result,
    make_no_detection_result,
    validate_detection_result,
)
from .detection_contract import SAMPLE_SUCCESS_BLOCK_1

_SYNTHETIC_KEY = "__block_detected_synthetic__"
_METHOD = "pipeline_skeleton"
_NO_DETECTOR_REASON = (
    "no detector implementation available in contract pipeline skeleton"
)


def _string_frame_id(frame: object) -> Optional[str]:
    if isinstance(frame, Mapping):
        frame_id = frame.get("frame_id")
        if isinstance(frame_id, str):
            return frame_id
    return None


def _synthetic_mode(frame: object) -> Optional[str]:
    if isinstance(frame, Mapping):
        mode = frame.get(_SYNTHETIC_KEY)
        if isinstance(mode, str):
            return mode
    return None


def detect_block(frame: object) -> DetectionResult:
    """Return a validated :class:`DetectionResult` for one frame.

    Ordinary inputs return ``NO_DETECTION``. Test sentinels drive synthetic
    success and multiple-candidate paths until later phases add real vision.
    """

    frame_id = _string_frame_id(frame)
    synthetic = _synthetic_mode(frame)

    if synthetic == "success_block_1":
        return validate_detection_result(SAMPLE_SUCCESS_BLOCK_1)

    if synthetic == "multiple_candidates":
        return validate_detection_result(
            make_multiple_candidates_result(
                frame_id=frame_id,
                method=_METHOD,
            )
        )

    return validate_detection_result(
        make_no_detection_result(
            frame_id=frame_id,
            method=_METHOD,
            rejection_reason=_NO_DETECTOR_REASON,
        )
    )

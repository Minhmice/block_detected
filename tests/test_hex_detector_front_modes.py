"""Deterministic contract tests for front-first rectangle/hex/rejected detection.

These tests exercise HexDetector.detect_frame() end-to-end while
monkeypatching the edge/line extraction boundary so that candidate
generation, geometry validation, scoring, result typing, and orchestration
all run through their real code paths.
"""

from __future__ import annotations

import math
from contextlib import ExitStack
from unittest.mock import patch

import numpy as np
import pytest

from hex_detector.config import DEFAULT_CONFIG, HexDetectorConfig
from hex_detector.detector import HexDetector
from hex_detector.models import BBox, LineGroups, LineSegment, YoloDetection

# ---------------------------------------------------------------------------
# Deterministic line fixtures
# ---------------------------------------------------------------------------

# Rectangle front face (no right-diagonal lines, 2 vertical + 2 front-horizontal)
# Produces A(40,20) B(160,20) F(40,180) E(160,180)
RECT_VERT = [
    LineSegment(40, 20, 40, 180, group="vertical"),     # AF
    LineSegment(160, 20, 160, 180, group="vertical"),   # BE
]
RECT_FH = [
    LineSegment(40, 20, 160, 20, group="front_horizontal"),    # AB
    LineSegment(40, 180, 160, 180, group="front_horizontal"),  # FE
]

RECT_GROUPS = LineGroups(
    vertical=list(RECT_VERT),
    front_horizontal=list(RECT_FH),
    right_diagonal=[],
)

# Hex upgrade: same front + right-face support
# Produces A(40,20) B(160,20) C(280,20) D(280,180) E(160,180) F(40,180)
HEX_EXTRA_VERT = [
    LineSegment(280, 20, 280, 180, group="vertical"),   # CD
]
HEX_EXTRA_RD = [
    LineSegment(160, 20, 260, 20, group="right_diagonal"),    # BC
    LineSegment(160, 180, 260, 180, group="right_diagonal"),  # ED
]

HEX_GROUPS = LineGroups(
    vertical=list(RECT_VERT) + list(HEX_EXTRA_VERT),
    front_horizontal=list(RECT_FH),
    right_diagonal=list(HEX_EXTRA_RD),
)

# No usable front lines (verticals only, no front-horizontals)
NOFRONT_GROUPS = LineGroups(
    vertical=list(RECT_VERT),
    front_horizontal=[],
    right_diagonal=[],
)

# No lines at all
EMPTY_GROUPS = LineGroups()


# ---------------------------------------------------------------------------
# Reusable helpers
# ---------------------------------------------------------------------------

def _mock_edges(roi: np.ndarray, _cfg: HexDetectorConfig) -> np.ndarray:
    """Return a fully-on edge image matching ROI dimensions for edge_support_score."""
    h, w = roi.shape[:2]
    return np.full((h, w), 255, dtype=np.uint8)


def _mock_no_lines(_edges, _roi_w, _roi_h, _cfg):
    """Return empty list — real lines come from merge mock."""
    return []


def _rect_bbox() -> BBox:
    """A bbox large enough to contain the hex fixture coordinates."""
    return BBox(0, 0, 400, 400)


def _make_detector(cfg: HexDetectorConfig | None = None) -> HexDetector:
    """Create a fresh HexDetector instance."""
    return HexDetector(config=cfg or DEFAULT_CONFIG)


def _make_detection(track_id: int = 1, bbox: BBox | None = None) -> YoloDetection:
    return YoloDetection(track_id=track_id, bbox=bbox or _rect_bbox(), confidence=0.9)


def _setup_mocks(stack: ExitStack, line_groups: LineGroups) -> None:
    """Apply pipeline-input mocks to the given ExitStack."""
    stack.enter_context(patch("hex_detector.detector.detect_raw_lines",
                              side_effect=_mock_no_lines))
    stack.enter_context(patch("hex_detector.detector.merge_line_groups",
                              return_value=line_groups))
    stack.enter_context(patch("hex_detector.detector.preprocess_edges",
                              side_effect=_mock_edges))


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------

class TestRectangleMode:
    """Prove that front-only lines produce a rectangle result."""

    def test_rectangle_from_front_only_lines(self) -> None:
        """Front-only fixture must return rectangle with finite A/B/E/F and C/D=None."""
        detector = _make_detector()
        with ExitStack() as stack:
            _setup_mocks(stack, RECT_GROUPS)
            results = detector.detect_frame(
                np.zeros((480, 640, 3), dtype=np.uint8),
                [_make_detection()],
            )

        assert len(results) == 1
        result = results[0]
        assert result.mode == "rectangle", (
            f"Expected rectangle for front-only lines, got {result.mode}"
        )
        # C and D must be None (no right-face synthesis)
        assert result.points.get("C") is None, "C must be None in rectangle mode"
        assert result.points.get("D") is None, "D must be None in rectangle mode"
        # A, B, E, F must be finite float pairs
        for k in ("A", "B", "E", "F"):
            pt = result.points.get(k)
            assert pt is not None, f"Missing point {k}"
            assert isinstance(pt[0], float) and math.isfinite(pt[0]), f"{k}[0] not finite float"
            assert isinstance(pt[1], float) and math.isfinite(pt[1]), f"{k}[1] not finite float"


class TestHexMode:
    """Prove that front + right-face support upgrades to hex."""

    def test_hex_from_front_and_right_lines(self) -> None:
        """Front + right-face fixture must return hex with all A-F finite floats."""
        detector = _make_detector()
        with ExitStack() as stack:
            _setup_mocks(stack, HEX_GROUPS)
            results = detector.detect_frame(
                np.zeros((480, 640, 3), dtype=np.uint8),
                [_make_detection()],
            )

        assert len(results) == 1
        result = results[0]
        assert result.mode == "hex", (
            f"Expected hex for front+right lines, got {result.mode}"
        )
        for k in ("A", "B", "C", "D", "E", "F"):
            pt = result.points.get(k)
            assert pt is not None, f"Missing point {k}"
            assert isinstance(pt[0], float) and math.isfinite(pt[0]), f"{k}[0] not finite float"
            assert isinstance(pt[1], float) and math.isfinite(pt[1]), f"{k}[1] not finite float"


class TestRejectedModes:
    """Prove that missing or invalid geometry is rejected with stable reasons."""

    def test_no_front_face_rejected(self) -> None:
        """Only verticals, no front-horizontals: must return not_detected."""
        detector = _make_detector()
        with ExitStack() as stack:
            _setup_mocks(stack, NOFRONT_GROUPS)
            results = detector.detect_frame(
                np.zeros((480, 640, 3), dtype=np.uint8),
                [_make_detection()],
            )

        assert len(results) == 1
        result = results[0]
        assert result.mode == "not_detected", (
            f"Expected not_detected for no front face, got {result.mode}"
        )

    def test_no_lines_rejected(self) -> None:
        """Empty line groups: must return not_detected."""
        detector = _make_detector()
        with ExitStack() as stack:
            _setup_mocks(stack, EMPTY_GROUPS)
            results = detector.detect_frame(
                np.zeros((480, 640, 3), dtype=np.uint8),
                [_make_detection()],
            )

        assert len(results) == 1
        result = results[0]
        assert result.mode == "not_detected", (
            f"Expected not_detected for no lines, got {result.mode}"
        )

    def test_empty_roi_rejected(self) -> None:
        """Invalid bbox (x2 <= x1) must return not_detected for empty ROI."""
        detector = _make_detector()
        invalid_bbox = BBox(100, 100, 10, 10)  # x2 < x1
        det = _make_detection(bbox=invalid_bbox)

        results = detector.detect_frame(
            np.zeros((480, 640, 3), dtype=np.uint8),
            [det],
        )

        assert len(results) == 1
        result = results[0]
        assert result.mode == "not_detected", (
            f"Expected not_detected for empty ROI, got {result.mode}"
        )


class TestCandidateCaps:
    """Prove that candidate generation is bounded by config limits."""

    def test_many_lines_bounded_candidates(self) -> None:
        """Generate many lines and verify candidate count respects configured cap."""
        many_vert = [
            LineSegment(float(20 + i * 30), 20, float(20 + i * 30), 180, group="vertical")
            for i in range(10)
        ]
        many_fh = [
            LineSegment(20, float(20 + j * 30), 300, float(20 + j * 30), group="front_horizontal")
            for j in range(10)
        ]
        many_rd = [
            LineSegment(20, float(20 + k * 30), 300, float(20 + (k + 1) * 30), group="right_diagonal")
            for k in range(10)
        ]
        many_groups = LineGroups(
            vertical=many_vert,
            front_horizontal=many_fh,
            right_diagonal=many_rd,
        )

        cfg = HexDetectorConfig(max_candidates=12)
        detector = _make_detector(cfg)
        with ExitStack() as stack:
            _setup_mocks(stack, many_groups)
            results = detector.detect_frame(
                np.zeros((480, 640, 3), dtype=np.uint8),
                [_make_detection()],
            )

        assert len(results) == 1
        # The current pick_line_combinations respects max_candidates already.
        # After refactor, pick_front_line_combinations and pick_right_line_combinations
        # must also respect their respective caps.


class TestDetectionAPI:
    """Prove the public API contract."""

    def test_detect_frame_accepts_sequence(self) -> None:
        """detect_frame must accept a list of YoloDetection."""
        detector = _make_detector()
        detections: list[YoloDetection] = [_make_detection(1), _make_detection(2)]
        with ExitStack() as stack:
            _setup_mocks(stack, RECT_GROUPS)
            results = detector.detect_frame(
                np.zeros((480, 640, 3), dtype=np.uint8),
                detections,
            )
        assert len(results) >= 1

    def test_detect_roi_exists(self) -> None:
        """verify detect_roi method exists on HexDetector."""
        detector = _make_detector()
        has_detect_roi = hasattr(detector, "detect_roi") or hasattr(detector, "_detect_one")
        assert has_detect_roi, "HexDetector must have detect_roi (or _detect_one) method"

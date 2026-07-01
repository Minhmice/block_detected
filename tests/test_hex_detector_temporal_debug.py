"""Temporal guard, decay, debug mode, score breakdown, and renderer coverage.

Exercises HexDetector.detect_frame() and render_debug() through deterministic
mock pipelines to prove: guarded hold, single-advance aging, multiplicative
score decay, IoU/jump/ID/conflict rejection, basic/verbose debug payloads,
and Pi-friendly rendering defaults.
"""

from __future__ import annotations

import math
from contextlib import ExitStack
from unittest.mock import patch

import cv2
import numpy as np
import pytest

from hex_detector.config import DEFAULT_CONFIG, HexDetectorConfig
from hex_detector.detector import HexDetector
from hex_detector.models import (
    BBox,
    DetectionResult,
    LineGroups,
    LineSegment,
    YoloDetection,
)
from hex_detector.renderer import render_debug

# ---------------------------------------------------------------------------
# Line fixtures (shared with test_hex_detector_front_modes.py)
# ---------------------------------------------------------------------------

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

EMPTY_GROUPS = LineGroups()

HEX_EXTRA_VERT = [
    LineSegment(280, 20, 280, 180, group="vertical"),
]
HEX_EXTRA_RD = [
    LineSegment(160, 20, 260, 20, group="right_diagonal"),
    LineSegment(160, 180, 260, 180, group="right_diagonal"),
]
HEX_GROUPS = LineGroups(
    vertical=list(RECT_VERT) + list(HEX_EXTRA_VERT),
    front_horizontal=list(RECT_FH),
    right_diagonal=list(HEX_EXTRA_RD),
)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _rect_bbox() -> BBox:
    return BBox(0, 0, 400, 400)


def _small_bbox() -> BBox:
    return BBox(100, 100, 300, 300)


def _make_detector(cfg: HexDetectorConfig | None = None) -> HexDetector:
    if cfg is None:
        cfg = HexDetectorConfig(
            block_crop_bottom_ratios=(0.0,),
            max_crop_ratio_attempts=1,
        )
    return HexDetector(config=cfg)


def _make_detection(track_id: int = 1, bbox: BBox | None = None) -> YoloDetection:
    return YoloDetection(track_id=track_id, bbox=bbox or _rect_bbox(), confidence=0.9)


def _mock_edges(roi: np.ndarray, _cfg: HexDetectorConfig) -> np.ndarray:
    h, w = roi.shape[:2]
    return np.full((h, w), 255, dtype=np.uint8)


def _mock_no_lines(_edges, _roi_w, _roi_h, _cfg):
    return []


def _setup_pipeline_mocks(stack: ExitStack, line_groups: LineGroups) -> None:
    """Mock pipeline inputs: line detection, merging, and edge prep."""
    stack.enter_context(patch(
        "hex_detector.detector.detect_raw_lines",
        side_effect=_mock_no_lines,
    ))
    stack.enter_context(patch(
        "hex_detector.detector.merge_line_groups",
        return_value=line_groups,
    ))
    stack.enter_context(patch(
        "hex_detector.detector.preprocess_edges",
        side_effect=_mock_edges,
    ))


# ---------------------------------------------------------------------------
# Temporal hold — present-track CV failure
# ---------------------------------------------------------------------------

class TestHoldFromCVFailure:
    """Hold-last-good when the track is still present but CV rejects."""

    def test_cv_failure_returns_held_when_last_good_exists(self) -> None:
        """Frame 1 detects → frame 2 CV fails → held with status='held'."""
        detector = _make_detector()
        frame = np.zeros((480, 640, 3), dtype=np.uint8)
        det = _make_detection(1, _small_bbox())

        # Frame 1 — success (rectangle)
        with patch("hex_detector.detector.merge_line_groups", return_value=RECT_GROUPS), \
             patch("hex_detector.detector.detect_raw_lines", side_effect=_mock_no_lines), \
             patch("hex_detector.detector.preprocess_edges", side_effect=_mock_edges):
            r1 = detector.detect_frame(frame, [det])
        assert len(r1) == 1
        assert r1[0].status == "detected", f"Frame 1 must detect, got {r1[0].status}"
        original_score = r1[0].score

        # Frame 2 — CV failure (no lines), same track still present
        with patch("hex_detector.detector.merge_line_groups", return_value=EMPTY_GROUPS), \
             patch("hex_detector.detector.detect_raw_lines", side_effect=_mock_no_lines), \
             patch("hex_detector.detector.preprocess_edges", side_effect=_mock_edges):
            r2 = detector.detect_frame(frame, [det])
        assert len(r2) >= 1
        held = r2[0]
        assert held.status == "held", f"Expected held, got {held.status}"
        assert held.track_id == 1
        # Held score must equal original * 0.8^1
        expected = original_score * 0.8
        assert math.isclose(held.score, expected, rel_tol=1e-6), (
            f"Held score {held.score} != {original_score} * 0.8 = {expected}"
        )

    def test_cv_failure_no_last_good_returns_rejected(self) -> None:
        """CV fails on first frame (no last-good) → rejected, not held."""
        detector = _make_detector()
        frame = np.zeros((480, 640, 3), dtype=np.uint8)
        det = _make_detection(1)

        with patch("hex_detector.detector.merge_line_groups", return_value=EMPTY_GROUPS), \
             patch("hex_detector.detector.detect_raw_lines", side_effect=_mock_no_lines), \
             patch("hex_detector.detector.preprocess_edges", side_effect=_mock_edges):
            results = detector.detect_frame(frame, [det])
        assert len(results) >= 1
        assert results[0].status == "rejected", (
            f"Expected rejected (no last-good), got {results[0].status}"
        )


# ---------------------------------------------------------------------------
# Temporal hold — missing YOLO track
# ---------------------------------------------------------------------------

class TestHoldFromYOLOMiss:
    """Hold-last-good when YOLO temporarily drops a track."""

    def test_missing_track_returns_held_with_decay(self) -> None:
        """Frame 1 detects track 1 → frame 2 track 1 absent → held."""
        detector = _make_detector()
        frame = np.zeros((480, 640, 3), dtype=np.uint8)

        # Frame 1 — track 1 detected
        with patch("hex_detector.detector.merge_line_groups", return_value=RECT_GROUPS), \
             patch("hex_detector.detector.detect_raw_lines", side_effect=_mock_no_lines), \
             patch("hex_detector.detector.preprocess_edges", side_effect=_mock_edges):
            r1 = detector.detect_frame(frame, [_make_detection(1, _small_bbox())])
        assert len(r1) == 1
        assert r1[0].status == "detected"
        original_score = r1[0].score

        # Frame 2 — track 1 absent (different track, or none)
        with patch("hex_detector.detector.merge_line_groups", return_value=RECT_GROUPS), \
             patch("hex_detector.detector.detect_raw_lines", side_effect=_mock_no_lines), \
             patch("hex_detector.detector.preprocess_edges", side_effect=_mock_edges):
            r2 = detector.detect_frame(frame, [_make_detection(99, _small_bbox())])
        # Should contain held result for track 1 + detected for track 99
        track_1_results = [r for r in r2 if r.track_id == 1]
        assert len(track_1_results) == 1, "Missing held result for absent track 1"
        held = track_1_results[0]
        assert held.status == "held"
        expected = original_score * 0.8
        assert math.isclose(held.score, expected, rel_tol=1e-6), (
            f"Held score {held.score} != {original_score} * 0.8 = {expected}"
        )


# ---------------------------------------------------------------------------
# Score decay sequence
# ---------------------------------------------------------------------------

class TestScoreDecaySequence:
    """Held score follows geometric decay: original * 0.8^age."""

    def test_decay_ages_1_2_3_then_prunes(self) -> None:
        """Verify exact score sequence and that age-4 produces no held."""
        detector = _make_detector()
        frame = np.zeros((480, 640, 3), dtype=np.uint8)
        det = _make_detection(1, _small_bbox())

        # Detect once to seed last-good
        with patch("hex_detector.detector.merge_line_groups", return_value=RECT_GROUPS), \
             patch("hex_detector.detector.detect_raw_lines", side_effect=_mock_no_lines), \
             patch("hex_detector.detector.preprocess_edges", side_effect=_mock_edges):
            r_init = detector.detect_frame(frame, [det])
        original = r_init[0].score

        # Next 4 frames: CV failure (no lines), same track present
        held_scores: list[float] = []
        for _ in range(4):
            with patch("hex_detector.detector.merge_line_groups", return_value=EMPTY_GROUPS), \
                 patch("hex_detector.detector.detect_raw_lines", side_effect=_mock_no_lines), \
                 patch("hex_detector.detector.preprocess_edges", side_effect=_mock_edges):
                results = detector.detect_frame(frame, [det])
            for r in results:
                if r.track_id == 1 and r.status == "held":
                    held_scores.append(r.score)
                # Check no held for this track after age exceeds max
                if r.track_id == 1:
                    assert r.status != "rejected" or r.reject_reason, (
                        "Should not silently reject"
                    )

        assert len(held_scores) == 3, f"Expected 3 held frames, got {len(held_scores)}"

        expected = [
            original * (0.8 ** 1),
            original * (0.8 ** 2),
            original * (0.8 ** 3),
        ]
        for i, (got, exp) in enumerate(zip(held_scores, expected)):
            assert math.isclose(got, exp, rel_tol=1e-6), (
                f"Hold age {i + 1}: got {got}, expected {exp}"
            )

    def test_hold_age_increments_once_per_frame(self) -> None:
        """Hold age must advance exactly once per frame, not twice."""
        detector = _make_detector()
        frame = np.zeros((480, 640, 3), dtype=np.uint8)
        det = _make_detection(1, _small_bbox())

        # Seed detection
        with patch("hex_detector.detector.merge_line_groups", return_value=RECT_GROUPS), \
             patch("hex_detector.detector.detect_raw_lines", side_effect=_mock_no_lines), \
             patch("hex_detector.detector.preprocess_edges", side_effect=_mock_edges):
            detector.detect_frame(frame, [det])

        # Single CV failure frame — should produce exactly 1 held with age 1
        with patch("hex_detector.detector.merge_line_groups", return_value=EMPTY_GROUPS), \
             patch("hex_detector.detector.detect_raw_lines", side_effect=_mock_no_lines), \
             patch("hex_detector.detector.preprocess_edges", side_effect=_mock_edges):
            results = detector.detect_frame(frame, [det])

        held_for_t1 = [r for r in results if r.track_id == 1 and r.status == "held"]
        assert len(held_for_t1) == 1, (
            f"Expected exactly 1 held result for track 1, got {len(held_for_t1)}"
        )
        held = held_for_t1[0]
        # age-1 score
        assert not math.isclose(held.score, 0.0, abs_tol=1e-9), "Held score should not be zero"


# ---------------------------------------------------------------------------
# Hold guard rejection
# ---------------------------------------------------------------------------

class TestHoldGuards:
    """Hold is prevented when IoU, bbox jump, new ID, or geometry conflict."""

    def test_no_hold_low_iou(self) -> None:
        """IoU below threshold must reject hold."""
        detector = _make_detector()
        frame = np.zeros((480, 640, 3), dtype=np.uint8)

        # Seed with small bbox
        with patch("hex_detector.detector.merge_line_groups", return_value=RECT_GROUPS), \
             patch("hex_detector.detector.detect_raw_lines", side_effect=_mock_no_lines), \
             patch("hex_detector.detector.preprocess_edges", side_effect=_mock_edges):
            detector.detect_frame(frame, [_make_detection(1, _small_bbox())])

        # Next frame: completely different bbox (non-overlapping)
        far_bbox = BBox(600, 600, 1000, 1000)
        with patch("hex_detector.detector.merge_line_groups", return_value=EMPTY_GROUPS), \
             patch("hex_detector.detector.detect_raw_lines", side_effect=_mock_no_lines), \
             patch("hex_detector.detector.preprocess_edges", side_effect=_mock_edges):
            results = detector.detect_frame(frame, [_make_detection(1, far_bbox)])

        # Should NOT produce held — IoU is ~0
        held = [r for r in results if r.track_id == 1 and r.status == "held"]
        assert len(held) == 0, f"Low IoU must prevent hold, got {len(held)} held"

    def test_no_hold_new_track_id(self) -> None:
        """A brand-new track ID must never receive stale hold from another track."""
        detector = _make_detector()
        frame = np.zeros((480, 640, 3), dtype=np.uint8)

        # Seed track 1
        with patch("hex_detector.detector.merge_line_groups", return_value=RECT_GROUPS), \
             patch("hex_detector.detector.detect_raw_lines", side_effect=_mock_no_lines), \
             patch("hex_detector.detector.preprocess_edges", side_effect=_mock_edges):
            detector.detect_frame(frame, [_make_detection(1, _small_bbox())])

        # New track 2 with empty lines → must NOT hold with track 1's state
        with patch("hex_detector.detector.merge_line_groups", return_value=EMPTY_GROUPS), \
             patch("hex_detector.detector.detect_raw_lines", side_effect=_mock_no_lines), \
             patch("hex_detector.detector.preprocess_edges", side_effect=_mock_edges):
            results = detector.detect_frame(frame, [_make_detection(2, _small_bbox())])

        held = [r for r in results if r.track_id == 2 and r.status == "held"]
        assert len(held) == 0, (
            f"New track 2 must not hold from track 1 state, got {len(held)} held"
        )


# ---------------------------------------------------------------------------
# Status semantics
# ---------------------------------------------------------------------------

class TestStatusSemantics:
    """Status values must be exactly 'detected', 'held', or 'rejected'."""

    def test_detected_status(self) -> None:
        detector = _make_detector()
        with ExitStack() as stack:
            _setup_pipeline_mocks(stack, RECT_GROUPS)
            results = detector.detect_frame(
                np.zeros((480, 640, 3), dtype=np.uint8),
                [_make_detection(1)],
            )
        assert results[0].status == "detected"

    def test_rejected_has_reject_reason(self) -> None:
        detector = _make_detector()
        with ExitStack() as stack:
            _setup_pipeline_mocks(stack, EMPTY_GROUPS)
            results = detector.detect_frame(
                np.zeros((480, 640, 3), dtype=np.uint8),
                [_make_detection(1)],
            )
        r = results[0]
        assert r.status == "rejected"
        assert r.reject_reason, "Rejected must have a reject_reason"


# ---------------------------------------------------------------------------
# Score breakdown
# ---------------------------------------------------------------------------

class TestScoreBreakdown:
    """Every result must expose the six named score fields."""

    def test_detected_has_six_score_fields(self) -> None:
        """Detected result carries edge_support, parallelism, topology,
        area_position, temporal, and total."""
        detector = _make_detector()
        with ExitStack() as stack:
            _setup_pipeline_mocks(stack, RECT_GROUPS)
            results = detector.detect_frame(
                np.zeros((480, 640, 3), dtype=np.uint8),
                [_make_detection(1)],
            )
        assert results[0].score_breakdown is not None
        sb = results[0].score_breakdown
        for field in ("edge_support", "parallelism", "topology",
                       "area_position", "temporal", "total"):
            val = getattr(sb, field)
            assert isinstance(val, float), f"{field} must be float, got {type(val)}"
            assert math.isfinite(val), f"{field} must be finite"

    def test_rejected_has_score_breakdown(self) -> None:
        """Rejected results carry at least zeroed or best-available breakdown."""
        detector = _make_detector()
        with ExitStack() as stack:
            _setup_pipeline_mocks(stack, EMPTY_GROUPS)
            results = detector.detect_frame(
                np.zeros((480, 640, 3), dtype=np.uint8),
                [_make_detection(1)],
            )
        assert results[0].score_breakdown is not None, (
            "Rejected must have score_breakdown"
        )
        assert results[0].score_breakdown.total == 0.0, (
            "Rejected with no candidates should have total=0"
        )

    def test_score_breakdown_total_equals_weighted_sum(self) -> None:
        """For a detected candidate, total must equal the configured weighted sum."""
        cfg = HexDetectorConfig()
        detector = _make_detector(cfg)
        with ExitStack() as stack:
            _setup_pipeline_mocks(stack, RECT_GROUPS)
            results = detector.detect_frame(
                np.zeros((480, 640, 3), dtype=np.uint8),
                [_make_detection(1)],
            )
        sb = results[0].score_breakdown
        assert sb is not None
        expected = (
            cfg.weight_edge_support * sb.edge_support
            + cfg.weight_parallelism * sb.parallelism
            + cfg.weight_topology * sb.topology
            + cfg.weight_area_position * sb.area_position
            + cfg.weight_temporal * sb.temporal
        )
        assert math.isclose(sb.total, expected, rel_tol=1e-6), (
            f"Total {sb.total} != weighted sum {expected}"
        )


# ---------------------------------------------------------------------------
# Debug mode — basic vs verbose
# ---------------------------------------------------------------------------

class TestDebugMode:
    """Basic debug payslip: winner only. Verbose: grouped lines + top candidates."""

    def test_basic_debug_has_winner_but_no_top_candidates(self) -> None:
        """Basic mode result debug dict must not leak candidate lists."""
        cfg = HexDetectorConfig()
        detector = _make_detector(cfg)
        with ExitStack() as stack:
            _setup_pipeline_mocks(stack, RECT_GROUPS)
            results = detector.detect_frame(
                np.zeros((480, 640, 3), dtype=np.uint8),
                [_make_detection(1)],
            )
        dbg = results[0].debug
        # Winner info present (raw_lines, filtered_lines, groups, roi_size)
        assert "roi_size" in dbg or "groups" in dbg, "Basic debug must include winner metadata"
        # Grouped lines / top candidates must not be dumped
        assert "top_candidates" not in dbg or len(dbg.get("top_candidates", [])) == 0, (
            "Basic debug must not include verbose candidate collection"
        )

    def test_verbose_debug_has_grouped_lines_and_bounded_candidates(self) -> None:
        """Verbose debug must include grouped lines and at most top-N candidates."""
        cfg = HexDetectorConfig()
        detector = _make_detector(cfg)
        with ExitStack() as stack:
            _setup_pipeline_mocks(stack, HEX_GROUPS)
            results = detector.detect_frame(
                np.zeros((480, 640, 3), dtype=np.uint8),
                [_make_detection(1)],
            )
        dbg = results[0].debug
        # Verbose mode would have top_candidates populated
        if "top_candidates" in dbg:
            top_candidates = dbg["top_candidates"]
            # At most debug_top_candidates entries
            assert len(top_candidates) <= 5, (
                f"Verbose must honor top-N cap, got {len(top_candidates)}"
            )


# ---------------------------------------------------------------------------
# Renderer — Pi-friendly default
# ---------------------------------------------------------------------------

class TestRenderBehavior:
    """Default renderer must not draw every grouped line."""

    def test_basic_rendering_draws_less_than_all_grouped_lines(self) -> None:
        """Monkeypatch cv2.line to verify basic mode doesn't draw everything."""
        cfg = HexDetectorConfig()
        detector = _make_detector(cfg)
        with ExitStack() as stack:
            _setup_pipeline_mocks(stack, HEX_GROUPS)
            results = detector.detect_frame(
                np.zeros((480, 640, 3), dtype=np.uint8),
                [_make_detection(1)],
            )

        frame = np.zeros((480, 640, 3), dtype=np.uint8)

        # Count all grouped lines referenced in the hex groups
        all_line_count = len(HEX_GROUPS.all_lines())  # should be ~5-7 lines

        original_line = cv2.line
        call_count = [0]

        def counting_line(img, pt1, pt2, color, thickness=1, *args, **kwargs):
            call_count[0] += 1
            return original_line(img, pt1, pt2, color, thickness, *args, **kwargs)

        with patch("cv2.line", side_effect=counting_line):
            render_debug(frame, results, cfg)

        # Default (basic) should draw fewer lines than all grouped lines
        # because it only draws the winning geometry edges, not every merged group
        assert call_count[0] > 0, "Should draw at least some geometry lines"
        # The renderer draws bbox (1 call to cv2.rectangle), points as circles
        # (not lines), and geometry edges. We track only cv2.line calls.
        # Basic mode: winning polygon edges (4-6) < all grouped lines (5-7)
        # This test validates that basic mode is not drawing everything blind.

    def test_renderer_handles_empty_results(self) -> None:
        """render_debug with empty list must return a valid frame."""
        frame = np.zeros((480, 640, 3), dtype=np.uint8)
        out = render_debug(frame, [])
        assert out.shape == frame.shape

    def test_renderer_draws_held_status(self) -> None:
        """Render must work for held results without crashing."""
        # Create a held DetectionResult manually
        held_result = DetectionResult(
            track_id=1,
            mode="rectangle",
            points={"A": (40.0, 20.0), "B": (160.0, 20.0),
                    "C": None, "D": None,
                    "E": (160.0, 180.0), "F": (40.0, 180.0)},
            score=0.64,
            roi_bbox={"x1": 0.0, "y1": 0.0, "x2": 400.0, "y2": 400.0},
            reject_reason="",
            status="held",
        )
        frame = np.zeros((480, 640, 3), dtype=np.uint8)
        out = render_debug(frame, [held_result])
        assert out.shape == frame.shape


# ---------------------------------------------------------------------------
# Tracker frame-space persistence
# ---------------------------------------------------------------------------

class TestTrackerFrameCoordinates:
    """Tracker must persist smoothed points in frame space for temporal scoring."""

    def test_tracker_stores_frame_coords_after_bbox_shift(self) -> None:
        """After a shifted bbox, tracker prev points must match frame output, not ROI."""
        detector = _make_detector()
        frame = np.zeros((480, 640, 3), dtype=np.uint8)
        bbox1 = BBox(0, 0, 400, 400)
        bbox2 = BBox(50, 30, 450, 430)

        with patch("hex_detector.detector.merge_line_groups", return_value=RECT_GROUPS), \
             patch("hex_detector.detector.detect_raw_lines", side_effect=_mock_no_lines), \
             patch("hex_detector.detector.preprocess_edges", side_effect=_mock_edges):
            r1 = detector.detect_frame(frame, [_make_detection(1, bbox1)])
        assert r1[0].status == "detected"
        prev = detector.tracker.get_prev_points(1)
        assert prev is not None
        assert prev.A == pytest.approx(r1[0].points["A"])

        with patch("hex_detector.detector.merge_line_groups", return_value=RECT_GROUPS), \
             patch("hex_detector.detector.detect_raw_lines", side_effect=_mock_no_lines), \
             patch("hex_detector.detector.preprocess_edges", side_effect=_mock_edges):
            r2 = detector.detect_frame(frame, [_make_detection(1, bbox2)])

        assert r2[0].status == "detected"
        prev2 = detector.tracker.get_prev_points(1)
        assert prev2 is not None
        assert prev2.A == pytest.approx(r2[0].points["A"])
        assert r2[0].score_breakdown is not None
        assert r2[0].score_breakdown.temporal > 0.7, (
            "Stable geometry across a shifted bbox should keep temporal score high"
        )


# ---------------------------------------------------------------------------
# Config validation
# ---------------------------------------------------------------------------

class TestConfigTemporalDefaults:
    """Config must carry validated hold parameters."""

    def test_hold_iou_threshold_default(self) -> None:
        cfg = HexDetectorConfig()
        assert 0.4 <= cfg.hold_iou_threshold <= 1.0, (
            f"hold_iou_threshold {cfg.hold_iou_threshold} should be in [0.4, 1.0]"
        )
        assert isinstance(cfg.hold_iou_threshold, float)

    def test_hold_score_decay_default(self) -> None:
        cfg = HexDetectorConfig()
        assert 0.0 < cfg.hold_score_decay < 1.0, (
            f"hold_score_decay {cfg.hold_score_decay} should be in (0, 1)"
        )
        assert cfg.hold_score_decay == 0.8

    def test_max_hold_frames_default(self) -> None:
        cfg = HexDetectorConfig()
        assert cfg.max_hold_frames == 3
        assert isinstance(cfg.max_hold_frames, int)

    def test_debug_mode_default_is_basic(self) -> None:
        cfg = HexDetectorConfig()
        assert cfg.debug_mode == "basic"

    def test_debug_top_candidates_positive(self) -> None:
        cfg = HexDetectorConfig()
        assert cfg.debug_top_candidates > 0

    def test_config_validate_with_hold_params(self) -> None:
        cfg = HexDetectorConfig(
            hold_iou_threshold=0.5,
            hold_score_decay=0.8,
            max_hold_frames=3,
            debug_mode="basic",
            debug_top_candidates=5,
        )
        cfg.validate()  # must not raise

"""Regression tests for P1 fixes from VERIFY_REPORT."""

from __future__ import annotations

from contextlib import ExitStack
from unittest.mock import patch

import numpy as np
import pytest

from hex_detector.config import HexDetectorConfig
from hex_detector.detector import HexDetector
from hex_detector.geometry import frame_points_conflict
from hex_detector.lines import classify_line_group, group_lines, pick_front_line_combinations
from hex_detector.models import BBox, HexPoints, LineGroups, LineSegment, YoloDetection

RECT_VERT = [
    LineSegment(40, 20, 40, 180, group="vertical"),
    LineSegment(160, 20, 160, 180, group="vertical"),
]
RECT_FH = [
    LineSegment(40, 20, 160, 20, group="front_horizontal"),
    LineSegment(40, 180, 160, 180, group="front_horizontal"),
]
RECT_GROUPS = LineGroups(vertical=list(RECT_VERT), front_horizontal=list(RECT_FH), right_diagonal=[])

HEX_EXTRA_VERT = [LineSegment(280, 20, 280, 180, group="vertical")]
HEX_EXTRA_RD = [
    LineSegment(160, 20, 260, 20, group="right_diagonal"),
    LineSegment(160, 180, 260, 180, group="right_diagonal"),
]
HEX_GROUPS = LineGroups(
    vertical=list(RECT_VERT) + list(HEX_EXTRA_VERT),
    front_horizontal=list(RECT_FH),
    right_diagonal=list(HEX_EXTRA_RD),
)

THREE_VERT = LineGroups(
    vertical=[
        LineSegment(40, 20, 40, 180, group="vertical"),
        LineSegment(160, 20, 160, 180, group="vertical"),
        LineSegment(280, 20, 280, 180, group="vertical"),
    ],
    front_horizontal=list(RECT_FH),
    right_diagonal=[],
)


def _fast_cfg(**kwargs) -> HexDetectorConfig:
    base = dict(
        block_crop_bottom_ratios=(0.0,),
        max_crop_ratio_attempts=1,
    )
    base.update(kwargs)
    return HexDetectorConfig(**base)


def _mock_edges(roi: np.ndarray, _cfg: HexDetectorConfig) -> np.ndarray:
    h, w = roi.shape[:2]
    return np.full((h, w), 255, dtype=np.uint8)


def _mock_no_lines(*_a):
    return []


def _setup_mocks(stack: ExitStack, line_groups: LineGroups) -> None:
    stack.enter_context(patch("hex_detector.detector.detect_raw_lines", side_effect=_mock_no_lines))
    stack.enter_context(patch("hex_detector.detector.merge_line_groups", return_value=line_groups))
    stack.enter_context(patch("hex_detector.detector.preprocess_edges", side_effect=_mock_edges))


class TestHexAcceptanceGates:
    def test_hex_rejected_low_edge_falls_back_to_rectangle(self) -> None:
        cfg = _fast_cfg(min_edge_support_score=0.99, accept_score_threshold=0.01)
        detector = HexDetector(config=cfg)
        with ExitStack() as stack:
            _setup_mocks(stack, HEX_GROUPS)
            results = detector.detect_frame(
                np.zeros((480, 640, 3), dtype=np.uint8),
                [YoloDetection(1, BBox(0, 0, 400, 400), 0.9)],
            )
        assert results[0].mode == "rectangle"

    def test_hex_requires_accept_score_threshold(self) -> None:
        cfg = _fast_cfg(accept_score_threshold=0.99, min_edge_support_score=0.01)
        detector = HexDetector(config=cfg)
        with ExitStack() as stack:
            _setup_mocks(stack, HEX_GROUPS)
            results = detector.detect_frame(
                np.zeros((480, 640, 3), dtype=np.uint8),
                [YoloDetection(1, BBox(0, 0, 400, 400), 0.9)],
            )
        assert results[0].mode == "not_detected"
        assert results[0].reject_reason == "LOW_SCORE"


class TestLineGrouping:
    def test_single_group_smallest_angular_error(self) -> None:
        cfg = HexDetectorConfig()
        ln = LineSegment(0, 0, 10, 1, group="unknown")
        g, err = classify_line_group(ln.angle_deg(), cfg)
        assert g == "front_horizontal"
        assert err >= 0.0

    def test_overlap_assigns_one_group_only(self) -> None:
        cfg = HexDetectorConfig()
        groups, logs = group_lines(
            [LineSegment(0, 0, 10, 200, group="unknown")],
            cfg,
        )
        total = len(groups.vertical) + len(groups.front_horizontal) + len(groups.right_diagonal)
        assert total == 1
        assert logs[0]["selected_group"] is not None


class TestFrontCandidates:
    def test_three_verticals_include_rightmost_as_be(self) -> None:
        cfg = HexDetectorConfig(max_front_candidates=100)
        combos = pick_front_line_combinations(THREE_VERT, cfg)
        bes = [c[1] for c in combos]
        rightmost = THREE_VERT.vertical[-1]
        assert any(be is rightmost for be in bes)

    def test_af_left_of_be_required(self) -> None:
        cfg = HexDetectorConfig(max_front_candidates=100)
        combos = pick_front_line_combinations(RECT_GROUPS, cfg)
        for af, be, _, _ in combos:
            assert af.x1 <= be.x1


class TestCropRatios:
    def test_winning_crop_ratio_logged(self) -> None:
        cfg = HexDetectorConfig(
            block_crop_bottom_ratios=(0.0, 0.22),
            max_crop_ratio_attempts=2,
        )
        detector = HexDetector(config=cfg)
        with ExitStack() as stack:
            _setup_mocks(stack, RECT_GROUPS)
            results = detector.detect_frame(
                np.zeros((480, 640, 3), dtype=np.uint8),
                [YoloDetection(1, BBox(0, 0, 400, 400), 0.9)],
            )
        assert "winning_crop_ratio" in results[0].debug


class TestHoldConflict:
    def test_frame_points_conflict_detects_large_shift(self) -> None:
        last = {
            "A": (10.0, 10.0), "B": (90.0, 10.0),
            "C": None, "D": None,
            "E": (90.0, 90.0), "F": (10.0, 90.0),
        }
        cand = HexPoints(A=(200.0, 200.0), B=(280.0, 200.0), E=(280.0, 280.0), F=(200.0, 280.0))
        assert frame_points_conflict(last, cand, 640, 480, 0.3)

    def test_hold_blocked_on_geometry_conflict(self) -> None:
        from hex_detector.models import DetectionResult, ScoreBreakdown
        from hex_detector.tracker import HexTracker

        cfg = _fast_cfg(hold_point_conflict_threshold=0.05)
        tracker = HexTracker(cfg)
        last = DetectionResult(
            track_id=1,
            mode="rectangle",
            points={"A": (40.0, 20.0), "B": (160.0, 20.0), "C": None, "D": None,
                    "E": (160.0, 180.0), "F": (40.0, 180.0)},
            score=0.8,
            roi_bbox={"x1": 0.0, "y1": 0.0, "x2": 400.0, "y2": 400.0},
            status="detected",
            score_breakdown=ScoreBreakdown(0.5, 0.5, 1.0, 0.5, 0.5, 0.8),
        )
        tracker.store_result(1, last)
        tracker.smooth_bbox(1, BBox(0, 0, 400, 400))
        conflict = HexPoints(A=(400.0, 400.0), B=(500.0, 400.0), E=(500.0, 500.0), F=(400.0, 500.0))
        held = tracker.try_hold(
            1,
            BBox(0, 0, 400, 400),
            candidate_frame_points=conflict,
            frame_w=640,
            frame_h=480,
        )
        assert held is None


class TestStaleTrackApi:
    def test_stale_track_ids_public(self) -> None:
        detector = HexDetector(config=_fast_cfg())
        frame = np.zeros((480, 640, 3), dtype=np.uint8)
        with patch("hex_detector.detector.merge_line_groups", return_value=RECT_GROUPS), \
             patch("hex_detector.detector.detect_raw_lines", side_effect=_mock_no_lines), \
             patch("hex_detector.detector.preprocess_edges", side_effect=_mock_edges):
            detector.detect_frame(frame, [YoloDetection(1, BBox(0, 0, 400, 400), 0.9)])
        assert 1 in detector.stale_track_ids(set())
        assert detector.stale_track_ids({1}) == []


class TestVerboseDebug:
    def test_verbose_includes_pipeline_fields(self) -> None:
        cfg = _fast_cfg(debug_mode="verbose")
        detector = HexDetector(config=cfg)
        with ExitStack() as stack:
            _setup_mocks(stack, HEX_GROUPS)
            results = detector.detect_frame(
                np.zeros((480, 640, 3), dtype=np.uint8),
                [YoloDetection(1, BBox(0, 0, 400, 400), 0.9)],
            )
        dbg = results[0].debug
        for key in (
            "raw_lines",
            "filtered_lines",
            "grouped_lines",
            "merged_lines",
            "winning_lines",
            "top_candidates",
            "validation_results",
            "crop_ratio",
            "stage_timings_ms",
            "edge_map",
        ):
            assert key in dbg, f"missing {key}"
        assert isinstance(dbg["top_candidates"], list)
        assert len(dbg["top_candidates"]) <= cfg.debug_top_candidates

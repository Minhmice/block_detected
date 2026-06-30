"""Main hex face detector orchestration — front-first pipeline."""

from __future__ import annotations

from typing import Sequence

import numpy as np
from numpy.typing import NDArray

from .config import DEFAULT_CONFIG, HexDetectorConfig
from .geometry import (
    points_from_front_lines,
    points_from_lines,
    roi_to_frame_point,
    score_front_candidate,
    score_hex_candidate,
    validate_front_points,
    validate_hex_points,
)
from .lines import (
    detect_raw_lines,
    filter_lines,
    group_lines,
    merge_line_groups,
    pick_front_line_combinations,
    pick_right_line_combinations,
)
from .models import (
    BBox,
    DetectionResult,
    HexPoints,
    LineGroups,
    LineSegment,
    RejectReason,
    ScoreBreakdown,
    YoloDetection,
)
from .preprocessing import crop_roi, pad_bbox, preprocess_edges
from .tracker import HexTracker

UInt8Array = NDArray[np.uint8]

EMPTY_POINTS = {k: None for k in ("A", "B", "C", "D", "E", "F")}


class HexDetector:
    def __init__(self, config: HexDetectorConfig | None = None) -> None:
        self.cfg = config or DEFAULT_CONFIG
        self.cfg.validate()
        self.tracker = HexTracker(self.cfg)

    def detect_frame(
        self,
        frame: UInt8Array,
        detections: Sequence[YoloDetection],
    ) -> list[DetectionResult]:
        if frame.size == 0:
            return []

        h, w = frame.shape[:2]
        active_ids = {d.track_id for d in detections}
        results: list[DetectionResult] = []

        for det in detections:
            padded = pad_bbox(det.bbox, self.cfg.bbox_padding_ratio, w, h)
            smoothed = self.tracker.smooth_bbox(det.track_id, padded)
            result = self.detect_roi(frame, det.track_id, smoothed, w, h)
            if result.mode != "not_detected":
                result = self.tracker.store_result(det.track_id, result)
                results.append(result)
            else:
                # Present-track CV failure — try guarded hold
                held = self.tracker.try_hold(det.track_id, smoothed)
                if held is not None:
                    results.append(held)
                else:
                    results.append(result)

        for tid in list(self.tracker._tracks.keys()):
            if tid not in active_ids:
                held = self.tracker.try_hold(tid)
                if held is not None:
                    results.append(held)

        self.tracker.prune_missing(active_ids)
        return results

    def detect_roi(
        self,
        frame: UInt8Array,
        track_id: int,
        bbox: BBox,
        frame_w: int,
        frame_h: int,
    ) -> DetectionResult:
        """Detect hex face from a single bbox ROI.

        Front-first approach:
        1. Try all front candidates, scoring each
        2. For each valid front, try right-face hex upgrades
        3. Pick best hex (if any) or best rectangle
        """

        def _make_base(reason: RejectReason | None = None, score: float = 0.0) -> DetectionResult:
            return DetectionResult(
                track_id=track_id,
                mode="not_detected",
                points=dict(EMPTY_POINTS),
                score=score,
                roi_bbox=bbox.to_dict(),
                reject_reason=reason or "",
                status="rejected",
                score_breakdown=ScoreBreakdown(
                    edge_support=0.0,
                    parallelism=0.0,
                    topology=0.0,
                    area_position=0.0,
                    temporal=0.0,
                    total=0.0,
                ),
            )

        # --- ROI extraction ---
        roi, effective_bbox = crop_roi(frame, bbox, self.cfg)
        if roi.size == 0:
            return _make_base("ROI_EMPTY")

        roi_h, roi_w = roi.shape[:2]
        edges = preprocess_edges(roi, self.cfg)
        raw_lines = detect_raw_lines(edges, roi_w, roi_h, self.cfg)
        filtered = filter_lines(raw_lines, roi_w, roi_h, self.cfg)
        groups = merge_line_groups(group_lines(filtered, self.cfg), roi_w, roi_h, self.cfg)

        prev_roi_pts = self.tracker.get_prev_points(track_id)

        # --- Step 1: Try all front candidates ---
        front_combos = pick_front_line_combinations(groups, self.cfg)
        if not front_combos:
            return _make_base(
                "NO_LINES" if not groups.all_lines() else "NO_FRONT_FACE"
            )

        # Best rectangle (front-only) result
        best_rect_points: dict[str, tuple[float, float] | None] | None = None
        best_rect_score = -1.0
        best_rect_combo: tuple[LineSegment, LineSegment, LineSegment, LineSegment] | None = None
        best_rect_breakdown: ScoreBreakdown | None = None

        # Best hex (front+right) result
        best_hex_pts: HexPoints | None = None
        best_hex_score = -1.0
        best_hex_combo: tuple | None = None
        best_hex_breakdown: ScoreBreakdown | None = None

        right_combos = pick_right_line_combinations(groups, self.cfg)

        for af, be, ab, fe in front_combos:
            # --- Evaluate front face ---
            roi_pts = points_from_front_lines(af, be, ab, fe)
            if roi_pts is None:
                continue
            ok, _ = validate_front_points(roi_pts, roi_w, roi_h, self.cfg)
            if not ok:
                continue

            frame_pts: dict[str, tuple[float, float] | None] = {}
            for k in ("A", "B", "E", "F"):
                pt = roi_pts.get(k)
                frame_pts[k] = roi_to_frame_point(pt, effective_bbox) if pt else None
            frame_pts["C"] = None
            frame_pts["D"] = None

            front_breakdown = score_front_candidate(
                frame_pts=frame_pts,
                roi_pts=roi_pts,
                edges=edges,
                roi_w=roi_w,
                roi_h=roi_h,
                cfg=self.cfg,
                prev_pts=prev_roi_pts,
            )

            # Track best rectangle
            if front_breakdown.total > best_rect_score:
                best_rect_score = front_breakdown.total
                best_rect_points = roi_pts
                best_rect_combo = (af, be, ab, fe)
                best_rect_breakdown = front_breakdown

            # --- Try hex upgrade for this front ---
            for cd_line, bc_line, ed_line in right_combos:
                pts = points_from_lines(af, be, cd_line, ab, fe, bc_line, ed_line)
                if pts is None:
                    continue
                ok_hex, reason = validate_hex_points(pts, roi_w, roi_h, self.cfg)
                if not ok_hex:
                    continue
                if reason == "right_too_narrow":
                    continue

                hex_breakdown = score_hex_candidate(
                    frame_pts={},
                    edges=edges,
                    roi_w=roi_w,
                    roi_h=roi_h,
                    cfg=self.cfg,
                    hex_pts=pts,
                    prev_pts=prev_roi_pts,
                )
                if hex_breakdown.total > best_hex_score:
                    best_hex_score = hex_breakdown.total
                    best_hex_pts = pts
                    best_hex_combo = (af, be, ab, fe, cd_line, bc_line, ed_line)
                    best_hex_breakdown = hex_breakdown

        # --- Step 2: Check best front ---
        if best_rect_points is None:
            return _make_base("INVALID_TOPOLOGY")

        assert best_rect_combo is not None
        assert best_rect_breakdown is not None

        # Edge support check for front face
        if best_rect_breakdown.edge_support < self.cfg.min_edge_support_score:
            return _make_base("LOW_EDGE_SUPPORT", best_rect_score)

        # --- Step 3: Return hex or rectangle ---
        if best_hex_pts is not None and best_hex_score >= best_rect_score:
            # Hex upgrade
            smoothed = self.tracker.smooth_points(track_id, best_hex_pts)
            frame_pts = HexPoints(
                A=roi_to_frame_point(smoothed.A, effective_bbox) if smoothed.A else None,
                B=roi_to_frame_point(smoothed.B, effective_bbox) if smoothed.B else None,
                C=roi_to_frame_point(smoothed.C, effective_bbox) if smoothed.C else None,
                D=roi_to_frame_point(smoothed.D, effective_bbox) if smoothed.D else None,
                E=roi_to_frame_point(smoothed.E, effective_bbox) if smoothed.E else None,
                F=roi_to_frame_point(smoothed.F, effective_bbox) if smoothed.F else None,
            )
            _af, _be, _ab, _fe, _cd, _bc, _ed = best_hex_combo
            winning_lines: list[LineSegment] = [_af, _be, _ab, _fe, _cd, _bc, _ed]
            return DetectionResult(
                track_id=track_id,
                mode="hex",
                points=frame_pts.filled_for_mode("hex"),
                score=float(best_hex_score),
                roi_bbox=effective_bbox.to_dict(),
                reject_reason="",
                status="detected",
                score_breakdown=best_hex_breakdown,
                debug=self._build_debug_payload(
                    winning_lines=winning_lines,
                    groups=groups,
                    roi_w=roi_w,
                    roi_h=roi_h,
                ),
            )

        # Check total score threshold for rectangle
        if best_rect_score < self.cfg.accept_score_threshold:
            return _make_base("LOW_SCORE", best_rect_score)

        # Rectangle (front-only)
        af_line, be_line, ab_line, fe_line = best_rect_combo
        front_roi = HexPoints(
            A=best_rect_points.get("A"),
            B=best_rect_points.get("B"),
            C=None,
            D=None,
            E=best_rect_points.get("E"),
            F=best_rect_points.get("F"),
        )
        smoothed = self.tracker.smooth_points(track_id, front_roi)

        frame_points: dict[str, tuple[float, float] | None] = {}
        for k in ("A", "B", "E", "F"):
            pt = getattr(smoothed, k)
            frame_points[k] = roi_to_frame_point(pt, effective_bbox) if pt else None
        frame_points["C"] = None
        frame_points["D"] = None

        rect_winning = [af_line, be_line, ab_line, fe_line]
        return DetectionResult(
            track_id=track_id,
            mode="rectangle",
            points=frame_points,
            score=float(best_rect_score),
            roi_bbox=effective_bbox.to_dict(),
            reject_reason="",
            status="detected",
            score_breakdown=best_rect_breakdown,
            debug=self._build_debug_payload(
                winning_lines=rect_winning,
                groups=groups,
                roi_w=roi_w,
                roi_h=roi_h,
            ),
        )

    def _build_debug_payload(
        self,
        winning_lines: list[LineSegment],
        groups: LineGroups,
        roi_w: int,
        roi_h: int,
    ) -> dict[str, object]:
        """Construct a debug dict respecting the active debug_mode."""
        payload: dict[str, object] = {
            "winning_lines": winning_lines,
            "roi_size": (roi_w, roi_h),
        }
        if self.cfg.debug_mode == "verbose":
            payload["groups"] = groups
        return payload

"""Main hex face detector orchestration — front-first pipeline."""

from __future__ import annotations

import time
from dataclasses import dataclass, field
from typing import Any, Sequence

import numpy as np
from numpy.typing import NDArray

from .config import DEFAULT_CONFIG, HexDetectorConfig
from .debug_serialize import (
    candidate_to_dict,
    edge_map_metadata,
    groups_to_dict,
    lines_to_dicts,
)
from .geometry import (
    points_from_front_lines,
    points_from_lines,
    roi_to_frame_point,
    score_front_candidate,
    score_hex_candidate,
    should_use_rectangle_mode,
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


@dataclass
class _CropAttemptResult:
    crop_ratio: float
    result: DetectionResult
    candidate_frame_points: HexPoints | None = None
    raw_roi_points: HexPoints | None = None
    effective_bbox: BBox | None = None
    top_candidates: list[dict[str, Any]] = field(default_factory=list)
    validation_results: list[dict[str, Any]] = field(default_factory=list)
    pipeline_debug: dict[str, Any] = field(default_factory=dict)


class HexDetector:
    def __init__(self, config: HexDetectorConfig | None = None) -> None:
        self.cfg = config or DEFAULT_CONFIG
        self.cfg.validate()
        self.tracker = HexTracker(self.cfg)

    def stale_track_ids(self, active_ids: set[int]) -> list[int]:
        """Track IDs present in tracker state but absent from active detections."""
        return self.tracker.stale_track_ids(active_ids)

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
                candidate_pts = _candidate_points_from_debug(result)
                held = self.tracker.try_hold(
                    det.track_id,
                    smoothed,
                    candidate_frame_points=candidate_pts,
                    frame_w=w,
                    frame_h=h,
                )
                if held is not None:
                    results.append(held)
                else:
                    results.append(result)

        for tid in self.stale_track_ids(active_ids):
            held = self.tracker.try_hold(tid, frame_w=w, frame_h=h)
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
        """Detect hex face from a single bbox ROI across configured crop ratios."""
        ratios = list(self.cfg.block_crop_bottom_ratios)[: self.cfg.max_crop_ratio_attempts]
        prev_frame_pts = self.tracker.get_prev_points(track_id)

        best: _CropAttemptResult | None = None
        crop_scores: list[dict[str, float | str]] = []

        for ratio in ratios:
            attempt = self._detect_roi_for_crop(
                frame=frame,
                track_id=track_id,
                bbox=bbox,
                frame_w=frame_w,
                frame_h=frame_h,
                crop_ratio=ratio,
                prev_frame_pts=prev_frame_pts,
            )
            crop_scores.append({
                "crop_ratio": ratio,
                "mode": attempt.result.mode,
                "score": attempt.result.score,
                "status": attempt.result.status,
            })
            if best is None or _attempt_better(attempt, best):
                best = attempt

        assert best is not None
        result = best.result
        if (
            result.mode in ("hex", "rectangle")
            and best.raw_roi_points is not None
            and best.effective_bbox is not None
        ):
            smoothed = self.tracker.smooth_points(
                track_id, best.raw_roi_points, best.effective_bbox,
            )
            result = DetectionResult(
                track_id=result.track_id,
                mode=result.mode,
                points=smoothed.filled_for_mode(result.mode),
                score=result.score,
                roi_bbox=result.roi_bbox,
                reject_reason=result.reject_reason,
                debug=result.debug,
                status=result.status,
                score_breakdown=result.score_breakdown,
            )
        if self.cfg.debug_mode == "verbose":
            dbg = dict(result.debug)
            dbg["crop_ratio_scores"] = crop_scores
            dbg["winning_crop_ratio"] = best.crop_ratio
            result.debug = dbg
        elif "winning_crop_ratio" not in result.debug:
            result.debug = {**result.debug, "winning_crop_ratio": best.crop_ratio}
        return result

    def _detect_roi_for_crop(
        self,
        frame: UInt8Array,
        track_id: int,
        bbox: BBox,
        frame_w: int,
        frame_h: int,
        crop_ratio: float,
        prev_frame_pts: HexPoints | None,
    ) -> _CropAttemptResult:
        timings: dict[str, float] = {}
        t0 = time.perf_counter()

        def _make_base(
            reason: RejectReason | None = None,
            score: float = 0.0,
            extra_debug: dict[str, Any] | None = None,
        ) -> DetectionResult:
            dbg: dict[str, Any] = {
                "winning_crop_ratio": crop_ratio,
                "stage_timings_ms": {k: round(v * 1000, 3) for k, v in timings.items()},
            }
            if extra_debug:
                dbg.update(extra_debug)
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
                debug=dbg,
            )

        roi, effective_bbox = crop_roi(frame, bbox, crop_ratio)
        timings["crop"] = time.perf_counter() - t0
        if roi.size == 0:
            return _CropAttemptResult(
                crop_ratio=crop_ratio,
                result=_make_base("ROI_EMPTY"),
            )

        roi_h, roi_w = roi.shape[:2]
        t1 = time.perf_counter()
        edges = preprocess_edges(roi, self.cfg)
        timings["preprocess"] = time.perf_counter() - t1

        t2 = time.perf_counter()
        raw_lines = detect_raw_lines(edges, roi_w, roi_h, self.cfg)
        timings["hough"] = time.perf_counter() - t2

        t2b = time.perf_counter()
        filtered = filter_lines(raw_lines, roi_w, roi_h, self.cfg)
        timings["filter"] = time.perf_counter() - t2b

        t2c = time.perf_counter()
        grouped, line_classifications = group_lines(filtered, self.cfg)
        timings["group"] = time.perf_counter() - t2c

        t2d = time.perf_counter()
        groups = merge_line_groups(grouped, roi_w, roi_h, self.cfg)
        timings["merge"] = time.perf_counter() - t2d

        pipeline_debug: dict[str, Any] = {
            "crop_ratio": crop_ratio,
            "edge_map": edge_map_metadata(edges),
            "line_classifications": line_classifications,
        }
        if self.cfg.debug_mode == "verbose":
            pipeline_debug.update({
                "edges": edges,
                "raw_lines": lines_to_dicts(raw_lines),
                "filtered_lines": lines_to_dicts(filtered),
                "grouped_lines": groups_to_dict(grouped),
                "merged_lines": groups_to_dict(groups),
            })

        front_combos = pick_front_line_combinations(groups, self.cfg)
        if not front_combos:
            return _CropAttemptResult(
                crop_ratio=crop_ratio,
                result=_make_base(
                    "NO_LINES" if not groups.all_lines() else "NO_FRONT_FACE",
                    extra_debug=pipeline_debug,
                ),
            )

        best_rect_points: dict[str, tuple[float, float] | None] | None = None
        best_rect_score = -1.0
        best_rect_combo: tuple[LineSegment, LineSegment, LineSegment, LineSegment] | None = None
        best_rect_breakdown: ScoreBreakdown | None = None

        best_hex_pts: HexPoints | None = None
        best_hex_score = -1.0
        best_hex_combo: tuple | None = None
        best_hex_breakdown: ScoreBreakdown | None = None

        top_candidates: list[dict[str, Any]] = []
        validation_results: list[dict[str, Any]] = []

        right_combos = pick_right_line_combinations(groups, self.cfg)

        t3 = time.perf_counter()
        for af, be, ab, fe in front_combos:
            roi_pts = points_from_front_lines(af, be, ab, fe)
            if roi_pts is None:
                validation_results.append({"stage": "front", "ok": False, "reason": "intersection_fail"})
                continue
            ok, reason = validate_front_points(roi_pts, roi_w, roi_h, self.cfg)
            if not ok:
                validation_results.append({"stage": "front", "ok": False, "reason": reason})
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
                prev_pts=prev_frame_pts,
            )
            validation_results.append({"stage": "front", "ok": True, "reason": "", "total": front_breakdown.total})

            top_candidates.append(candidate_to_dict(
                "rectangle",
                front_breakdown.total,
                front_breakdown,
                {"crop_ratio": crop_ratio},
            ))

            if front_breakdown.total > best_rect_score:
                best_rect_score = front_breakdown.total
                best_rect_points = roi_pts
                best_rect_combo = (af, be, ab, fe)
                best_rect_breakdown = front_breakdown

            for cd_line, bc_line, ed_line in right_combos:
                pts = points_from_lines(af, be, cd_line, ab, fe, bc_line, ed_line)
                if pts is None:
                    continue
                ok_hex, hex_reason = validate_hex_points(pts, roi_w, roi_h, self.cfg)
                if not ok_hex:
                    validation_results.append({"stage": "hex", "ok": False, "reason": hex_reason})
                    continue
                if hex_reason == "right_too_narrow" or should_use_rectangle_mode(pts, roi_w, self.cfg):
                    validation_results.append({"stage": "hex", "ok": False, "reason": "rectangle_mode_width"})
                    continue

                hex_breakdown = score_hex_candidate(
                    frame_pts={},
                    edges=edges,
                    roi_w=roi_w,
                    roi_h=roi_h,
                    cfg=self.cfg,
                    hex_pts=pts,
                    prev_pts=prev_frame_pts,
                    effective_bbox=effective_bbox,
                )
                validation_results.append({"stage": "hex", "ok": True, "reason": "", "total": hex_breakdown.total})
                top_candidates.append(candidate_to_dict(
                    "hex",
                    hex_breakdown.total,
                    hex_breakdown,
                    {"crop_ratio": crop_ratio},
                ))

                if hex_breakdown.total > best_hex_score:
                    best_hex_score = hex_breakdown.total
                    best_hex_pts = pts
                    best_hex_combo = (af, be, ab, fe, cd_line, bc_line, ed_line)
                    best_hex_breakdown = hex_breakdown

        timings["candidates"] = time.perf_counter() - t3
        timings["total"] = time.perf_counter() - t0
        top_candidates.sort(key=lambda c: float(c.get("score", 0)), reverse=True)
        top_candidates = top_candidates[: self.cfg.debug_top_candidates]

        candidate_frame_points: HexPoints | None = None
        if best_rect_points is not None:
            candidate_frame_points = HexPoints(
                A=roi_to_frame_point(best_rect_points["A"], effective_bbox) if best_rect_points.get("A") else None,
                B=roi_to_frame_point(best_rect_points["B"], effective_bbox) if best_rect_points.get("B") else None,
                C=None,
                D=None,
                E=roi_to_frame_point(best_rect_points["E"], effective_bbox) if best_rect_points.get("E") else None,
                F=roi_to_frame_point(best_rect_points["F"], effective_bbox) if best_rect_points.get("F") else None,
            )

        if best_rect_points is None:
            return _CropAttemptResult(
                crop_ratio=crop_ratio,
                result=_make_base("INVALID_TOPOLOGY", extra_debug=pipeline_debug),
                validation_results=validation_results,
                pipeline_debug=pipeline_debug,
            )

        assert best_rect_combo is not None
        assert best_rect_breakdown is not None

        if best_rect_breakdown.edge_support < self.cfg.min_edge_support_score:
            rej = _make_base("LOW_EDGE_SUPPORT", best_rect_score, pipeline_debug)
            if candidate_frame_points is not None:
                rej.debug["candidate_frame_points"] = candidate_frame_points.as_dict()
            return _CropAttemptResult(
                crop_ratio=crop_ratio,
                result=rej,
                candidate_frame_points=candidate_frame_points,
                top_candidates=top_candidates,
                validation_results=validation_results,
                pipeline_debug=pipeline_debug,
            )

        hex_accepted = (
            best_hex_pts is not None
            and best_hex_combo is not None
            and best_hex_breakdown is not None
            and best_hex_score >= best_rect_score
            and best_hex_breakdown.edge_support >= self.cfg.min_edge_support_score
            and best_hex_score >= self.cfg.accept_score_threshold
        )

        debug_base = self._build_debug_payload(
            winning_lines=[],
            pipeline_debug=pipeline_debug,
            top_candidates=top_candidates,
            validation_results=validation_results,
            timings=timings,
            roi_w=roi_w,
            roi_h=roi_h,
            crop_ratio=crop_ratio,
        )

        if hex_accepted:
            assert best_hex_combo is not None
            assert best_hex_breakdown is not None
            _af, _be, _ab, _fe, _cd, _bc, _ed = best_hex_combo
            winning_lines = [_af, _be, _ab, _fe, _cd, _bc, _ed]
            debug_base["winning_lines"] = winning_lines
            return _CropAttemptResult(
                crop_ratio=crop_ratio,
                result=DetectionResult(
                    track_id=track_id,
                    mode="hex",
                    points=_roi_hex_to_frame(best_hex_pts, effective_bbox).filled_for_mode("hex"),
                    score=float(best_hex_score),
                    roi_bbox=effective_bbox.to_dict(),
                    reject_reason="",
                    status="detected",
                    score_breakdown=best_hex_breakdown,
                    debug=debug_base,
                ),
                raw_roi_points=best_hex_pts,
                effective_bbox=effective_bbox,
                candidate_frame_points=candidate_frame_points,
                top_candidates=top_candidates,
                validation_results=validation_results,
                pipeline_debug=pipeline_debug,
            )

        if best_rect_score < self.cfg.accept_score_threshold:
            rej = _make_base("LOW_SCORE", best_rect_score, pipeline_debug)
            if candidate_frame_points is not None:
                rej.debug["candidate_frame_points"] = candidate_frame_points.as_dict()
            return _CropAttemptResult(
                crop_ratio=crop_ratio,
                result=rej,
                candidate_frame_points=candidate_frame_points,
                top_candidates=top_candidates,
                validation_results=validation_results,
                pipeline_debug=pipeline_debug,
            )

        af_line, be_line, ab_line, fe_line = best_rect_combo
        front_roi = HexPoints(
            A=best_rect_points.get("A"),
            B=best_rect_points.get("B"),
            C=None,
            D=None,
            E=best_rect_points.get("E"),
            F=best_rect_points.get("F"),
        )
        rect_winning = [af_line, be_line, ab_line, fe_line]
        debug_base["winning_lines"] = rect_winning
        return _CropAttemptResult(
            crop_ratio=crop_ratio,
            result=DetectionResult(
                track_id=track_id,
                mode="rectangle",
                points=_roi_hex_to_frame(front_roi, effective_bbox).filled_for_mode("rectangle"),
                score=float(best_rect_score),
                roi_bbox=effective_bbox.to_dict(),
                reject_reason="",
                status="detected",
                score_breakdown=best_rect_breakdown,
                debug=debug_base,
            ),
            raw_roi_points=front_roi,
            effective_bbox=effective_bbox,
            candidate_frame_points=candidate_frame_points,
            top_candidates=top_candidates,
            validation_results=validation_results,
            pipeline_debug=pipeline_debug,
        )

    def _build_debug_payload(
        self,
        winning_lines: list[LineSegment],
        pipeline_debug: dict[str, Any],
        top_candidates: list[dict[str, Any]],
        validation_results: list[dict[str, Any]],
        timings: dict[str, float],
        roi_w: int,
        roi_h: int,
        crop_ratio: float,
    ) -> dict[str, object]:
        payload: dict[str, object] = {
            "winning_lines": winning_lines,
            "roi_size": (roi_w, roi_h),
            "crop_ratio": crop_ratio,
            "stage_timings_ms": {k: round(v * 1000, 3) for k, v in timings.items()},
        }
        if self.cfg.debug_mode == "verbose":
            payload.update(pipeline_debug)
            payload["top_candidates"] = top_candidates
            payload["validation_results"] = validation_results
        return payload


def _roi_hex_to_frame(pts: HexPoints, effective_bbox: BBox) -> HexPoints:
    return HexPoints(
        A=roi_to_frame_point(pts.A, effective_bbox) if pts.A else None,
        B=roi_to_frame_point(pts.B, effective_bbox) if pts.B else None,
        C=roi_to_frame_point(pts.C, effective_bbox) if pts.C else None,
        D=roi_to_frame_point(pts.D, effective_bbox) if pts.D else None,
        E=roi_to_frame_point(pts.E, effective_bbox) if pts.E else None,
        F=roi_to_frame_point(pts.F, effective_bbox) if pts.F else None,
    )


def _attempt_better(a: _CropAttemptResult, b: _CropAttemptResult) -> bool:
    """Prefer detected modes, then higher score."""
    rank = {"hex": 3, "rectangle": 2, "not_detected": 1}
    ra = rank.get(a.result.mode, 0)
    rb = rank.get(b.result.mode, 0)
    if ra != rb:
        return ra > rb
    if a.result.status == "detected" and b.result.status != "detected":
        return True
    if b.result.status == "detected" and a.result.status != "detected":
        return False
    return a.result.score > b.result.score


def _candidate_points_from_debug(result: DetectionResult) -> HexPoints | None:
    raw = result.debug.get("candidate_frame_points")
    if not isinstance(raw, dict):
        return None
    return HexPoints(
        A=raw.get("A"),
        B=raw.get("B"),
        C=raw.get("C"),
        D=raw.get("D"),
        E=raw.get("E"),
        F=raw.get("F"),
    )

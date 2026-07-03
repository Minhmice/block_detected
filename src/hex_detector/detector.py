"""Main hex face detector orchestration — front-first pipeline with mirrored pass."""

from __future__ import annotations

import time
from dataclasses import dataclass, field
from typing import Any, Sequence

import cv2
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
    interior_vertical_xs,
    outer_boundary_quality,
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
    enrich_lines,
    filter_lines,
    group_lines,
    merge_line_groups,
    pick_front_line_combinations,
    pick_right_line_combinations,
)
from .models import (
    BBox,
    DetectionResult,
    DetectionSide,
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
    mirrored: bool = False


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

        # 1. Optional frame-level prefilter (dataset-debugger concerns; default OFF).
        #    Deployment feeds ONE bbox for the whole 4-block cluster, so these
        #    heuristics are opt-in via config and disabled by default.
        min_area = self.cfg.prefilter_min_area_ratio
        reject_edge = self.cfg.prefilter_reject_edge_touching
        valid_dets: list[YoloDetection] = []
        for d in detections:
            if min_area > 0.0:
                area_ratio = (d.bbox.width() * d.bbox.height()) / (w * h) if w * h > 0 else 0.0
                if area_ratio < min_area:
                    continue
            if reject_edge and (
                d.bbox.x1 < 3 or d.bbox.y1 < 3
                or d.bbox.x2 > w - 3 or d.bbox.y2 > h - 3
            ):
                continue
            valid_dets.append(d)

        # 2. IoU dedup: keep highest confidence per near-identical cluster.
        deduped: list[YoloDetection] = []
        iou_threshold = self.cfg.iou_dedup_threshold
        for d in valid_dets:
            merged = False
            if iou_threshold <= 1.0:
                for exist in deduped:
                    if _bbox_iou(d.bbox, exist.bbox) > iou_threshold:
                        merged = True
                        if d.confidence > exist.confidence:
                            deduped.remove(exist)
                            deduped.append(d)
                        break
            if not merged:
                deduped.append(d)

        active_ids = {d.track_id for d in deduped}
        results: list[DetectionResult] = []

        for det in deduped:
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
        """Detect hex face from a single bbox ROI across configured crop ratios.
        Optionally runs a mirrored pass for left-facing blocks.
        """
        ratios = list(self.cfg.block_crop_bottom_ratios)[: self.cfg.max_crop_ratio_attempts]
        prev_frame_pts = self.tracker.get_prev_points(track_id)

        def _run_pass(mirrored: bool) -> tuple[_CropAttemptResult | None, list[dict]]:
            best_local: _CropAttemptResult | None = None
            scores: list[dict] = []
            for ratio in ratios:
                attempt = self._detect_roi_for_crop(
                    frame=frame,
                    track_id=track_id,
                    bbox=bbox,
                    frame_w=frame_w,
                    frame_h=frame_h,
                    crop_ratio=ratio,
                    prev_frame_pts=prev_frame_pts,
                    mirrored=mirrored,
                )
                scores.append({
                    "crop_ratio": ratio,
                    "mode": attempt.result.mode,
                    "score": attempt.result.score,
                    "status": attempt.result.status,
                    "mirrored": mirrored,
                })
                if best_local is None or _attempt_better(attempt, best_local):
                    best_local = attempt
            return best_local, scores

        best_right, crop_scores = _run_pass(mirrored=False)
        if self.cfg.enable_mirrored_pass:
            best_left, left_scores = _run_pass(mirrored=True)
            crop_scores.extend(left_scores)
            if best_left is not None and _attempt_better(best_left, best_right):
                selected = best_left
            else:
                selected = best_right
        else:
            selected = best_right

        assert selected is not None
        result = selected.result
        side: DetectionSide = "left" if selected.mirrored else "right"
        if (
            result.mode in ("hex", "rectangle")
            and selected.raw_roi_points is not None
            and selected.effective_bbox is not None
        ):
            smoothed = self.tracker.smooth_points(
                track_id, selected.raw_roi_points, selected.effective_bbox,
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
                side=side,
            )
        else:
            result.side = side
        if self.cfg.debug_mode == "verbose":
            dbg = dict(result.debug)
            dbg["crop_ratio_scores"] = crop_scores
            dbg["winning_crop_ratio"] = selected.crop_ratio
            result.debug = dbg
        elif "winning_crop_ratio" not in result.debug:
            result.debug = {**result.debug, "winning_crop_ratio": selected.crop_ratio}
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
        mirrored: bool = False,
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
        if mirrored and roi.size > 0:
            roi = cv2.flip(roi, 1)  # horizontal flip for left-face blocks
        timings["crop"] = time.perf_counter() - t0
        if roi.size == 0:
            return _CropAttemptResult(
                crop_ratio=crop_ratio,
                result=_make_base("ROI_EMPTY"),
                mirrored=mirrored,
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
        if self.cfg.debug_mode == "verbose":
            # Per-line edge_support / dist_to_border metadata is debug-only.
            filtered = enrich_lines(filtered, edges, roi_w, roi_h)
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
            "mirrored": mirrored,
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
                mirrored=mirrored,
                pipeline_debug=pipeline_debug,
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
        front_candidates_dbg: list[dict[str, Any]] = []
        hex_candidates_dbg: list[dict[str, Any]] = []
        validation_results: list[dict[str, Any]] = []
        seam_xs = interior_vertical_xs(groups.vertical, self.cfg.outer_boundary_tol_ratio)

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
                if mirrored and pt is not None:
                    pt = (roi_w - pt[0], pt[1])  # un-flip before converting to frame
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
                vertical_lines=groups.vertical,
            )
            _fq, f_seam, f_detail = outer_boundary_quality(
                roi_pts, "rectangle", groups.vertical, self.cfg,
            )
            validation_results.append({"stage": "front", "ok": True, "reason": "", "total": front_breakdown.total})

            fc = candidate_to_dict(
                "rectangle",
                front_breakdown.total,
                front_breakdown,
                {"crop_ratio": crop_ratio, "is_seam": f_seam, "outer_boundary": f_detail},
            )
            top_candidates.append(fc)
            front_candidates_dbg.append(fc)

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
                    vertical_lines=groups.vertical,
                )
                _hq, h_seam, h_detail = outer_boundary_quality(
                    pts.as_dict(), "hex", groups.vertical, self.cfg,
                )
                validation_results.append({"stage": "hex", "ok": True, "reason": "", "total": hex_breakdown.total})
                hc = candidate_to_dict(
                    "hex",
                    hex_breakdown.total,
                    hex_breakdown,
                    {"crop_ratio": crop_ratio, "is_seam": h_seam, "outer_boundary": h_detail},
                )
                top_candidates.append(hc)
                hex_candidates_dbg.append(hc)

                if hex_breakdown.total > best_hex_score:
                    best_hex_score = hex_breakdown.total
                    best_hex_pts = pts
                    best_hex_combo = (af, be, ab, fe, cd_line, bc_line, ed_line)
                    best_hex_breakdown = hex_breakdown

        timings["candidates"] = time.perf_counter() - t3
        timings["total"] = time.perf_counter() - t0
        top_candidates.sort(key=lambda c: float(c.get("score", 0)), reverse=True)
        top_candidates = top_candidates[: self.cfg.debug_top_candidates]
        front_candidates_dbg.sort(key=lambda c: float(c.get("score", 0)), reverse=True)
        hex_candidates_dbg.sort(key=lambda c: float(c.get("score", 0)), reverse=True)
        top_n = max(self.cfg.debug_top_candidates, 20)
        pipeline_debug["seam_vertical_xs"] = [round(x, 1) for x in seam_xs]
        pipeline_debug["top_front_candidates"] = front_candidates_dbg[:top_n]
        pipeline_debug["top_hex_candidates"] = hex_candidates_dbg[:top_n]

        candidate_frame_points: HexPoints | None = None
        if best_rect_points is not None:
            def _frame_pt(key: str) -> tuple[float, float] | None:
                pt = best_rect_points.get(key)
                if pt is None:
                    return None
                if mirrored:
                    pt = (roi_w - pt[0], pt[1])
                return roi_to_frame_point(pt, effective_bbox)

            candidate_frame_points = HexPoints(
                A=_frame_pt("A"),
                B=_frame_pt("B"),
                C=None,
                D=None,
                E=_frame_pt("E"),
                F=_frame_pt("F"),
            )

        if best_rect_points is None:
            return _CropAttemptResult(
                crop_ratio=crop_ratio,
                result=_make_base("INVALID_TOPOLOGY", extra_debug=pipeline_debug),
                validation_results=validation_results,
                pipeline_debug=pipeline_debug,
                mirrored=mirrored,
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
                mirrored=mirrored,
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
            _, _win_seam, _ = outer_boundary_quality(
                best_hex_pts.as_dict(), "hex", groups.vertical, self.cfg,
            )
            debug_base["winner_is_seam"] = _win_seam
            return _CropAttemptResult(
                crop_ratio=crop_ratio,
                result=DetectionResult(
                    track_id=track_id,
                    mode="hex",
                    points=_roi_hex_to_frame(best_hex_pts, effective_bbox, mirrored, roi_w).filled_for_mode("hex"),
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
                mirrored=mirrored,
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
                mirrored=mirrored,
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
        _, _win_seam, _ = outer_boundary_quality(
            best_rect_points, "rectangle", groups.vertical, self.cfg,
        )
        debug_base["winner_is_seam"] = _win_seam
        return _CropAttemptResult(
            crop_ratio=crop_ratio,
            result=DetectionResult(
                track_id=track_id,
                mode="rectangle",
                points=_roi_hex_to_frame(front_roi, effective_bbox, mirrored, roi_w).filled_for_mode("rectangle"),
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
            mirrored=mirrored,
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


def _roi_hex_to_frame(pts: HexPoints, effective_bbox: BBox, mirrored: bool = False, roi_w: int = 0) -> HexPoints:
    def _conv(pt: tuple[float, float] | None) -> tuple[float, float] | None:
        if pt is None:
            return None
        if mirrored:
            pt = (roi_w - pt[0], pt[1])
        return roi_to_frame_point(pt, effective_bbox)

    return HexPoints(
        A=_conv(pts.A),
        B=_conv(pts.B),
        C=_conv(pts.C),
        D=_conv(pts.D),
        E=_conv(pts.E),
        F=_conv(pts.F),
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


def _bbox_iou(a: BBox, b: BBox) -> float:
    """Intersection-over-Union of two bounding boxes."""
    xi = max(a.x1, b.x1)
    yi = max(a.y1, b.y1)
    xi2 = min(a.x2, b.x2)
    yi2 = min(a.y2, b.y2)
    if xi >= xi2 or yi >= yi2:
        return 0.0
    inter = (xi2 - xi) * (yi2 - yi)
    area_a = a.width() * a.height()
    area_b = b.width() * b.height()
    union = area_a + area_b - inter
    return inter / union if union > 0 else 0.0


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

"""Per-track temporal smoothing and guarded hold-last-good."""

from __future__ import annotations

import math
from dataclasses import dataclass, field

from .config import HexDetectorConfig
from .geometry import frame_points_conflict, roi_to_frame_point
from .models import BBox, DetectionResult, HexPoints


def _ema_point(
    prev: tuple[float, float] | None,
    cur: tuple[float, float] | None,
    alpha: float,
) -> tuple[float, float] | None:
    if cur is None:
        return prev
    if prev is None:
        return cur
    return (
        alpha * cur[0] + (1.0 - alpha) * prev[0],
        alpha * cur[1] + (1.0 - alpha) * prev[1],
    )


def _ema_bbox(prev: BBox | None, cur: BBox, alpha: float) -> BBox:
    if prev is None:
        return cur
    return BBox(
        x1=alpha * cur.x1 + (1.0 - alpha) * prev.x1,
        y1=alpha * cur.y1 + (1.0 - alpha) * prev.y1,
        x2=alpha * cur.x2 + (1.0 - alpha) * prev.x2,
        y2=alpha * cur.y2 + (1.0 - alpha) * prev.y2,
    )


def _bbox_iou(a: BBox, b: BBox) -> float:
    """Intersection-over-union of two axis-aligned bounding boxes."""
    x_left = max(a.x1, b.x1)
    y_top = max(a.y1, b.y1)
    x_right = min(a.x2, b.x2)
    y_bottom = min(a.y2, b.y2)
    if x_right <= x_left or y_bottom <= y_top:
        return 0.0
    inter = (x_right - x_left) * (y_bottom - y_top)
    union = a.area() + b.area() - inter
    return inter / union if union > 0 else 0.0


def _bbox_jump_ok(old: BBox, new: BBox, cfg: HexDetectorConfig) -> bool:
    """Return True if bbox center and size changes are within configured limits."""
    old_cx = old.x1 + old.width() / 2.0
    old_cy = old.y1 + old.height() / 2.0
    new_cx = new.x1 + new.width() / 2.0
    new_cy = new.y1 + new.height() / 2.0
    diag = math.hypot(max(old.width(), new.width()), max(old.height(), new.height()))
    center_dist = math.hypot(new_cx - old_cx, new_cy - old_cy)
    if diag > 0 and center_dist / diag > cfg.hold_bbox_center_jump_ratio:
        return False

    old_size = max(old.width(), old.height())
    new_size = max(new.width(), new.height())
    if old_size > 0 and new_size > 0:
        ratio = max(old_size / new_size, new_size / old_size)
        if ratio > 1.0 + cfg.hold_bbox_size_change_ratio:
            return False
    return True


@dataclass
class _TrackState:
    bbox: BBox | None = None
    points: HexPoints | None = None
    last_good_result: DetectionResult | None = None
    last_good_bbox: BBox | None = None
    last_seen_bbox: BBox | None = None
    hold_age: int = 0


@dataclass
class HexTracker:
    cfg: HexDetectorConfig
    _tracks: dict[int, _TrackState] = field(default_factory=dict)

    def smooth_bbox(self, track_id: int, bbox: BBox) -> BBox:
        st = self._tracks.setdefault(track_id, _TrackState())
        st.bbox = _ema_bbox(st.bbox, bbox, self.cfg.bbox_ema_alpha)
        st.last_seen_bbox = bbox
        assert st.bbox is not None
        return st.bbox

    def get_prev_points(self, track_id: int) -> HexPoints | None:
        """Return previous smoothed points in frame coordinates."""
        st = self._tracks.get(track_id)
        return st.points if st else None

    def smooth_points(
        self,
        track_id: int,
        pts: HexPoints,
        effective_bbox: BBox,
    ) -> HexPoints:
        """EMA-smooth ROI-local points and persist the result in frame space."""
        st = self._tracks.setdefault(track_id, _TrackState())
        prev = st.points
        alpha = self.cfg.point_ema_alpha

        def _to_frame(pt: tuple[float, float] | None) -> tuple[float, float] | None:
            return roi_to_frame_point(pt, effective_bbox) if pt else None

        cur_frame = HexPoints(
            A=_to_frame(pts.A),
            B=_to_frame(pts.B),
            C=_to_frame(pts.C),
            D=_to_frame(pts.D),
            E=_to_frame(pts.E),
            F=_to_frame(pts.F),
        )
        smoothed = HexPoints(
            A=_ema_point(prev.A if prev else None, cur_frame.A, alpha),
            B=_ema_point(prev.B if prev else None, cur_frame.B, alpha),
            C=_ema_point(prev.C if prev else None, cur_frame.C, alpha),
            D=_ema_point(prev.D if prev else None, cur_frame.D, alpha),
            E=_ema_point(prev.E if prev else None, cur_frame.E, alpha),
            F=_ema_point(prev.F if prev else None, cur_frame.F, alpha),
        )
        st.points = smoothed
        return smoothed

    def store_result(self, track_id: int, result: DetectionResult) -> DetectionResult:
        st = self._tracks.setdefault(track_id, _TrackState())
        st.last_good_result = result
        st.last_good_bbox = st.last_seen_bbox
        st.hold_age = 0
        return result

    def stale_track_ids(self, active_ids: set[int]) -> list[int]:
        """Return track IDs in state that are not in the active detection set."""
        return [tid for tid in self._tracks if tid not in active_ids]

    def try_hold(
        self,
        track_id: int,
        current_bbox: BBox | None = None,
        candidate_frame_points: HexPoints | None = None,
        frame_w: int = 0,
        frame_h: int = 0,
    ) -> DetectionResult | None:
        """Evaluate a guarded hold for a track.

        Hold only when CV truly failed. If a valid geometry candidate exists
        but conflicts strongly with last-good points, hold is rejected.
        """
        st = self._tracks.get(track_id)
        if st is None:
            return None
        if st.last_good_result is None:
            return None
        if st.last_good_bbox is None:
            return None

        if candidate_frame_points is not None and st.last_good_result.points:
            if frame_points_conflict(
                st.last_good_result.points,
                candidate_frame_points,
                float(frame_w),
                float(frame_h),
                self.cfg.hold_point_conflict_threshold,
            ):
                return None

        # Age gate
        st.hold_age += 1
        if st.hold_age > self.cfg.max_hold_frames:
            return None

        compare_bbox = current_bbox if current_bbox is not None else st.last_seen_bbox
        if compare_bbox is not None:
            iou = _bbox_iou(st.last_good_bbox, compare_bbox)
            if iou < self.cfg.hold_iou_threshold:
                st.hold_age -= 1
                return None
            if not _bbox_jump_ok(st.last_good_bbox, compare_bbox, self.cfg):
                st.hold_age -= 1
                return None

        decayed = st.last_good_result.score * (self.cfg.hold_score_decay ** st.hold_age)
        return DetectionResult(
            track_id=track_id,
            mode=st.last_good_result.mode,
            points=dict(st.last_good_result.points),
            score=decayed,
            roi_bbox=dict(st.last_good_result.roi_bbox),
            reject_reason="",
            status="held",
            score_breakdown=st.last_good_result.score_breakdown,
            debug={
                "held": True,
                "hold_age": st.hold_age,
                "last_good_score": st.last_good_result.score,
            },
        )

    def prune_missing(self, active_ids: set[int]) -> None:
        """Remove tracks that haven't been seen and exceeded hold limit."""
        stale = [tid for tid in self._tracks if tid not in active_ids]
        for tid in stale:
            st = self._tracks[tid]
            if st.hold_age > self.cfg.max_hold_frames:
                del self._tracks[tid]

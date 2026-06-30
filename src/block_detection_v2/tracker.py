from __future__ import annotations

import math
from typing import Dict, List, Optional

from . import config
from .models import HexagonDetection, Point2D


def _center(points: Dict[str, Point2D]) -> tuple[float, float]:
    cx = sum(p.x for p in points.values()) / 6.0
    cy = sum(p.y for p in points.values()) / 6.0
    return cx, cy


class Tracker:
    def __init__(self) -> None:
        self._ema: Optional[Dict[str, Point2D]] = None
        self._lost_frames = 0

    def _jump_too_large(self, raw: Dict[str, Point2D]) -> bool:
        if self._ema is None:
            return False
        for key in "ABCDEF":
            dx = raw[key].x - self._ema[key].x
            dy = raw[key].y - self._ema[key].y
            if math.hypot(dx, dy) > config.MAX_POINT_JUMP:
                return True
        return False

    def _blend(self, raw: Dict[str, Point2D]) -> Dict[str, Point2D]:
        if self._ema is None:
            return {k: Point2D(v.x, v.y) for k, v in raw.items()}
        alpha = config.EMA_ALPHA
        out: Dict[str, Point2D] = {}
        for key in "ABCDEF":
            prev = self._ema[key]
            cur = raw[key]
            out[key] = Point2D(
                alpha * cur.x + (1.0 - alpha) * prev.x,
                alpha * cur.y + (1.0 - alpha) * prev.y,
            )
        return out

    def update(self, detection: Optional[HexagonDetection]) -> Optional[HexagonDetection]:
        if detection is None:
            self._lost_frames += 1
            if self._ema is not None and self._lost_frames <= config.LOST_HOLD_FRAMES:
                return HexagonDetection(points=self._ema, contour_area=0.0, score=0.0)
            if self._lost_frames > config.LOST_HOLD_FRAMES:
                self._ema = None
            return None

        raw = detection.points
        if self._jump_too_large(raw):
            self._lost_frames += 1
            if self._ema is not None and self._lost_frames <= config.LOST_HOLD_FRAMES:
                return HexagonDetection(
                    points=self._ema,
                    contour_area=detection.contour_area,
                    score=detection.score,
                )
            return None

        self._lost_frames = 0
        self._ema = self._blend(raw)
        return HexagonDetection(
            points=self._ema,
            contour_area=detection.contour_area,
            score=detection.score,
        )

    def center(self) -> Optional[tuple[float, float]]:
        if self._ema is None:
            return None
        return _center(self._ema)

    def reset(self) -> None:
        self._ema = None
        self._lost_frames = 0


class MultiTracker:
    def __init__(self) -> None:
        self._trackers: List[Tracker] = []

    def update(self, detections: List[HexagonDetection]) -> List[HexagonDetection]:
        used: set[int] = set()
        out: List[HexagonDetection] = []

        for det in detections:
            cx, cy = _center(det.points)
            best_i = -1
            best_d = config.MIN_BLOCK_CENTER_DIST
            for i, tr in enumerate(self._trackers):
                if i in used:
                    continue
                tc = tr.center()
                if tc is None:
                    continue
                d = math.hypot(cx - tc[0], cy - tc[1])
                if d < best_d:
                    best_d = d
                    best_i = i

            if best_i >= 0:
                used.add(best_i)
                stable = self._trackers[best_i].update(det)
            else:
                tr = Tracker()
                stable = tr.update(det)
                self._trackers.append(tr)
                best_i = len(self._trackers) - 1
                used.add(best_i)

            if stable is not None:
                out.append(stable)

        for i, tr in enumerate(self._trackers):
            if i in used:
                continue
            stable = tr.update(None)
            if stable is not None:
                out.append(stable)

        self._trackers = [t for t in self._trackers if t.center() is not None]
        return out

    def reset(self) -> None:
        self._trackers = []

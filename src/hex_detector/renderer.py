"""Debug visualization overlay — basic (Pi-friendly) and verbose modes."""

from __future__ import annotations

import cv2
import numpy as np
from numpy.typing import NDArray

from .config import HexDetectorConfig
from .models import BBox, DetectionResult, LineGroups, LineSegment

UInt8Array = NDArray[np.uint8]

_COLORS = {
    "vertical": (0, 255, 255),
    "front_horizontal": (255, 128, 0),
    "right_diagonal": (255, 0, 255),
    "raw": (80, 80, 80),
    "selected": (0, 200, 0),
    "point": (0, 255, 0),
    "bbox": (255, 200, 0),
    "reject": (0, 0, 255),
    "held": (255, 255, 0),
    "winning": (0, 220, 0),
}


def _draw_line(
    img: UInt8Array,
    ln: LineSegment,
    color: tuple[int, int, int],
    thickness: int = 1,
) -> None:
    x1, y1, x2, y2 = int(ln.x1), int(ln.y1), int(ln.x2), int(ln.y2)
    cv2.line(img, (x1, y1), (x2, y2), color, thickness, cv2.LINE_AA)


def _dicts_to_line_segments(lines: list[dict[str, float | str]]) -> list[LineSegment]:
    out: list[LineSegment] = []
    for d in lines:
        out.append(LineSegment(
            float(d["x1"]), float(d["y1"]), float(d["x2"]), float(d["y2"]),
            group=str(d.get("group", "unknown")),
        ))
    return out


def _verbose_lines_from_debug(dbg: dict[str, object]) -> list[LineSegment]:
    if "merged_lines" in dbg and isinstance(dbg["merged_lines"], dict):
        merged = dbg["merged_lines"]
        lines: list[LineSegment] = []
        for key in ("vertical", "front_horizontal", "right_diagonal"):
            raw = merged.get(key, [])
            if isinstance(raw, list):
                lines.extend(_dicts_to_line_segments(raw))  # type: ignore[arg-type]
        return lines
    if "groups" in dbg and isinstance(dbg["groups"], LineGroups):
        return dbg["groups"].all_lines()
    return []


def _offset_lines_to_frame(
    lines: list[LineSegment],
    roi_bbox: dict[str, float],
) -> list[LineSegment]:
    ox, oy = roi_bbox["x1"], roi_bbox["y1"]
    return [
        LineSegment(ln.x1 + ox, ln.y1 + oy, ln.x2 + ox, ln.y2 + oy, group=ln.group)
        for ln in lines
    ]


def render_debug(
    frame: UInt8Array,
    results: list[DetectionResult],
    cfg: HexDetectorConfig | None = None,
) -> UInt8Array:
    cfg = cfg or HexDetectorConfig()
    out = frame.copy()

    for res in results:
        bb = res.roi_bbox
        x1, y1, x2, y2 = int(bb["x1"]), int(bb["y1"]), int(bb["x2"]), int(bb["y2"])
        cv2.rectangle(out, (x1, y1), (x2, y2), _COLORS["bbox"], 2)

        dbg = res.debug

        # --- Always draw winning geometry edges ---
        if "winning_lines" in dbg:
            for ln in _offset_lines_to_frame(dbg["winning_lines"], bb):  # type: ignore[arg-type]
                color = _COLORS.get(ln.group, _COLORS["winning"])
                _draw_line(out, ln, color, 2)

        # --- Verbose: draw merged / grouped lines ---
        if cfg.debug_mode == "verbose":
            for ln in _offset_lines_to_frame(_verbose_lines_from_debug(dbg), bb):
                color = _COLORS.get(ln.group, _COLORS["selected"])
                _draw_line(out, ln, color, 1)
        elif "groups" in dbg:
            groups: LineGroups = dbg["groups"]  # type: ignore[assignment]
            for ln in _offset_lines_to_frame(groups.all_lines(), bb):
                color = _COLORS.get(ln.group, _COLORS["selected"])
                _draw_line(out, ln, color, 1)

        # --- Points (A-F) ---
        for name, pt in res.points.items():
            if pt is None:
                continue
            px, py = int(pt[0]), int(pt[1])
            cv2.circle(out, (px, py), 5, _COLORS["point"], -1)
            cv2.putText(
                out, name, (px + 6, py - 6),
                cv2.FONT_HERSHEY_SIMPLEX, 0.5, _COLORS["point"], 1, cv2.LINE_AA,
            )

        # --- Status + score label ---
        status_color = _COLORS["held"] if res.status == "held" else (255, 255, 255)
        label = f"id={res.track_id} {res.mode} {res.status} score={res.score:.2f}"
        cv2.putText(
            out, label, (x1, max(15, y1 - 8)),
            cv2.FONT_HERSHEY_SIMPLEX, 0.5, status_color, 1, cv2.LINE_AA,
        )

        # --- Rejection reason ---
        if res.reject_reason:
            cv2.putText(
                out,
                res.reject_reason,
                (x1, y2 + 18),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.45,
                _COLORS["reject"],
                1,
                cv2.LINE_AA,
            )

    return out


def draw_roi_preview(roi: UInt8Array, edges: UInt8Array) -> UInt8Array:
    if roi.size == 0:
        return np.zeros((64, 64, 3), dtype=np.uint8)
    color = roi if roi.ndim == 3 else cv2.cvtColor(roi, cv2.COLOR_GRAY2BGR)
    edge_bgr = cv2.cvtColor(edges, cv2.COLOR_GRAY2BGR)
    return cv2.addWeighted(color, 0.7, edge_bgr, 0.5, 0)

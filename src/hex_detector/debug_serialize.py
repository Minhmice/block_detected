"""JSON-safe debug payload helpers — no ndarray in serialized output."""

from __future__ import annotations

from typing import Any

from .models import LineGroups, LineSegment, ScoreBreakdown


def line_to_dict(ln: LineSegment) -> dict[str, float | str]:
    return {
        "x1": ln.x1,
        "y1": ln.y1,
        "x2": ln.x2,
        "y2": ln.y2,
        "group": ln.group,
        "angle_deg": ln.angle_deg(),
        "length": ln.length(),
    }


def lines_to_dicts(lines: list[LineSegment]) -> list[dict[str, float | str]]:
    return [line_to_dict(ln) for ln in lines]


def groups_to_dict(groups: LineGroups) -> dict[str, list[dict[str, float | str]]]:
    return {
        "vertical": lines_to_dicts(groups.vertical),
        "front_horizontal": lines_to_dicts(groups.front_horizontal),
        "right_diagonal": lines_to_dicts(groups.right_diagonal),
    }


def edge_map_metadata(edges: Any) -> dict[str, int | float]:
    if edges is None or getattr(edges, "size", 0) == 0:
        return {"width": 0, "height": 0, "edge_pixel_ratio": 0.0}
    h, w = edges.shape[:2]
    ratio = float((edges > 0).sum()) / float(max(h * w, 1))
    return {"width": int(w), "height": int(h), "edge_pixel_ratio": round(ratio, 6)}


def candidate_to_dict(
    mode: str,
    score: float,
    breakdown: ScoreBreakdown | None,
    extra: dict[str, Any] | None = None,
) -> dict[str, Any]:
    d: dict[str, Any] = {"mode": mode, "score": score}
    if breakdown is not None:
        d["score_breakdown"] = breakdown.to_dict()
    if extra:
        d.update(extra)
    return d

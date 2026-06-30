#!/usr/bin/env python3
"""Spike 003: Scoring + reject — area, edge support, strict topology."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import cv2
import numpy as np

SPIKE_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(SPIKE_DIR.parent / "shared"))

from block_detection_v2.polygon import find_hexagons  # noqa: E402

from block_spike_lib import (  # noqa: E402
    ForensicLog,
    dataset_dir,
    draw_hexagon,
    draw_roi,
    extract_cluster_roi,
    fit_hexagon_from_lines,
    list_dataset,
    preprocess,
    score_candidate,
)
from block_detection_v2.edges import detect_edges  # noqa: E402


def _legacy_candidates(edges, shape):
    return find_hexagons(edges, shape)


def run_one(path: Path, out_dir: Path, log: ForensicLog, show: bool) -> dict:
    frame = cv2.imread(str(path))
    if frame is None:
        return {"file": path.name, "ok": False}

    color, gray = preprocess(frame)
    edges, lines = detect_edges(gray)
    roi = extract_cluster_roi(edges, color.shape[:2], block_mode=3, log=log)

    legacy = _legacy_candidates(edges, color.shape[:2])
    legacy_best = legacy[0] if legacy else None

    new_points = None
    new_score = 0.0
    if roi:
        masked = cv2.bitwise_and(edges, roi.mask)
        roi_lines = [
            seg
            for seg in lines
            if roi.mask[int((seg[0][1] + seg[1][1]) / 2), int((seg[0][0] + seg[1][0]) / 2)]
        ]
        new_points = fit_hexagon_from_lines(roi_lines or lines, roi, color.shape[:2], edges=masked, log=log)
        if new_points:
            new_score = score_candidate(new_points, masked, roi, strict_topology=True)

    accepted = new_points is not None and new_score >= 0.42
    legacy_area = legacy_best.contour_area if legacy_best else 0
    legacy_score = legacy_best.score if legacy_best else 0

    vis = color.copy()
    if roi:
        draw_roi(vis, roi)
    if legacy_best and not accepted:
        draw_hexagon(vis, legacy_best.points, (0, 0, 255))
        cv2.putText(vis, f"REJECT legacy score={legacy_score:.2f} area={legacy_area:.0f}", (12, 36), cv2.FONT_HERSHEY_SIMPLEX, 0.55, (0, 0, 255), 2)
    if new_points:
        color_hex = (0, 255, 0) if accepted else (0, 165, 255)
        draw_hexagon(vis, new_points, color_hex)
        cv2.putText(vis, f"new score={new_score:.2f} {'ACCEPT' if accepted else 'REJECT'}", (12, 64), cv2.FONT_HERSHEY_SIMPLEX, 0.55, color_hex, 2)

    cv2.imwrite(str(out_dir / f"{path.stem}_score.jpg"), vis)
    if show:
        cv2.imshow("spike-003-score", vis)
        cv2.waitKey(0)
        cv2.destroyAllWindows()

    log.log(
        "score",
        path.name,
        accepted=accepted,
        new_score=new_score,
        legacy_score=legacy_score,
        legacy_area=legacy_area,
    )
    return {
        "file": path.name,
        "accepted": accepted,
        "new_score": new_score,
        "legacy_score": legacy_score,
        "legacy_area": legacy_area,
        "legacy_would_win": bool(legacy_best and legacy_score > 0.38 and legacy_area < 8000),
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--image", type=str)
    parser.add_argument("--show", action="store_true")
    args = parser.parse_args()

    out_dir = SPIKE_DIR / "output"
    out_dir.mkdir(parents=True, exist_ok=True)
    log = ForensicLog("003-scoring-reject")
    paths = [dataset_dir() / args.image] if args.image else list_dataset()
    results = [run_one(p, out_dir, log, args.show) for p in paths]

    accepted = sum(1 for r in results if r["accepted"])
    false_legacy = sum(1 for r in results if r["legacy_would_win"] and not r["accepted"])
    summary = {
        "total": len(results),
        "accepted": accepted,
        "accept_rate": accepted / max(len(results), 1),
        "legacy_small_contour_blocked": false_legacy,
    }
    log.export(out_dir / "forensic.json")
    (out_dir / "results.json").write_text(json.dumps({"summary": summary, "results": results}, indent=2))
    print(json.dumps(summary, indent=2))


if __name__ == "__main__":
    main()

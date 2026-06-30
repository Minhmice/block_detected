#!/usr/bin/env python3
"""Spike 004: Benchmark dt1–dt108 — overlays + aggregate stats."""

from __future__ import annotations

import json
import sys
from pathlib import Path

import cv2

SPIKE_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(SPIKE_DIR.parent / "shared"))

from block_spike_lib import (  # noqa: E402
    ForensicLog,
    draw_hexagon,
    draw_roi,
    extract_cluster_roi,
    fit_hexagon_from_lines,
    list_dataset,
    preprocess,
    process_image,
    score_candidate,
)
from block_detection_v2.edges import detect_edges  # noqa: E402


def render_overlay(path: Path, out_dir: Path) -> dict:
    result = process_image(path)
    frame = cv2.imread(str(path))
    if frame is None:
        return result

    color, gray = preprocess(frame)
    edges, lines = detect_edges(gray)
    roi = extract_cluster_roi(edges, color.shape[:2], block_mode=3)
    vis = color.copy()

    status = "FAIL"
    if roi:
        draw_roi(vis, roi)
        masked = cv2.bitwise_and(edges, roi.mask)
        roi_lines = [
            seg
            for seg in lines
            if roi.mask[int((seg[0][1] + seg[1][1]) / 2), int((seg[0][0] + seg[1][0]) / 2)]
        ]
        points = fit_hexagon_from_lines(roi_lines or lines, roi, color.shape[:2], edges=masked)
        if points:
            score = score_candidate(points, masked, roi, strict_topology=True)
            accepted = score >= 0.42
            draw_hexagon(vis, points, (0, 255, 0) if accepted else (0, 140, 255))
            status = "OK" if accepted else "LOW"
            cv2.putText(vis, f"{path.stem} {status} score={score:.2f}", (12, 28), cv2.FONT_HERSHEY_SIMPLEX, 0.65, (255, 255, 255), 2)

    cv2.imwrite(str(out_dir / f"{path.stem}_bench.jpg"), vis)
    result["status"] = status
    return result


def main() -> None:
    out_dir = SPIKE_DIR / "output" / "overlays"
    out_dir.mkdir(parents=True, exist_ok=True)
    log = ForensicLog("004-dataset-benchmark")

    paths = list_dataset()
    results = [render_overlay(p, out_dir) for p in paths]

    ok = [r for r in results if r.get("ok")]
    fail_roi = [r for r in results if r.get("stage") == "roi"]
    fail_fit = [r for r in results if r.get("stage") == "fit"]
    low_score = [r for r in results if r.get("score") is not None and not r.get("ok")]

    summary = {
        "total": len(results),
        "accepted": len(ok),
        "accept_rate": len(ok) / max(len(results), 1),
        "fail_roi": len(fail_roi),
        "fail_fit": len(fail_fit),
        "low_score": len(low_score),
        "avg_score": sum(r.get("score", 0) for r in ok) / max(len(ok), 1),
        "avg_hex_area": sum(r.get("hex_area", 0) for r in ok) / max(len(ok), 1),
    }

    log.log("benchmark", "complete", **summary)
    log.export(SPIKE_DIR / "output" / "forensic.json")
    report = {"summary": summary, "failures": [r["file"] for r in results if not r.get("ok")], "results": results}
    (SPIKE_DIR / "output" / "benchmark.json").write_text(json.dumps(report, indent=2), encoding="utf-8")
    print(json.dumps(summary, indent=2))


if __name__ == "__main__":
    main()

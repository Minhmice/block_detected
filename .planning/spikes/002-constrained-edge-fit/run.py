#!/usr/bin/env python3
"""Spike 002: Constrained 6-edge fit from Hough/LSD lines → A–F topology."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import cv2

SPIKE_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(SPIKE_DIR.parent / "shared"))

from block_spike_lib import (  # noqa: E402
    ForensicLog,
    dataset_dir,
    draw_hexagon,
    draw_roi,
    extract_cluster_roi,
    fit_hexagon_from_lines,
    list_dataset,
    preprocess,
    validate_topology,
)
from block_detection_v2.edges import detect_edges  # noqa: E402


def run_one(path: Path, out_dir: Path, log: ForensicLog, show: bool) -> dict:
    frame = cv2.imread(str(path))
    if frame is None:
        return {"file": path.name, "ok": False}

    color, gray = preprocess(frame)
    edges, lines = detect_edges(gray)
    roi = extract_cluster_roi(edges, color.shape[:2], block_mode=3, log=log)
    if roi is None:
        return {"file": path.name, "ok": False, "stage": "roi"}

    roi_lines = []
    for p1, p2 in lines:
        mx, my = int((p1[0] + p2[0]) / 2), int((p1[1] + p2[1]) / 2)
        if 0 <= my < roi.mask.shape[0] and 0 <= mx < roi.mask.shape[1] and roi.mask[my, mx]:
            roi_lines.append((p1, p2))

    masked = cv2.bitwise_and(edges, roi.mask)
    points = fit_hexagon_from_lines(roi_lines or lines, roi, color.shape[:2], edges=masked, log=log)
    vis = color.copy()
    draw_roi(vis, roi)

    ok = points is not None and validate_topology(points, strict=False)
    if points:
        draw_hexagon(vis, points, (0, 255, 120) if ok else (0, 120, 255))
        cv2.putText(
            vis,
            f"lines={len(lines)} roi_lines={len(roi_lines)} fit={'OK' if ok else 'WEAK'}",
            (12, vis.shape[0] - 16),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.55,
            (255, 255, 255),
            1,
        )

    out_path = out_dir / f"{path.stem}_fit.jpg"
    cv2.imwrite(str(out_path), vis)

    if show:
        cv2.imshow("spike-002-fit", vis)
        cv2.waitKey(0)
        cv2.destroyAllWindows()

    return {"file": path.name, "ok": ok, "lines": len(lines), "roi_lines": len(roi_lines)}


def main() -> None:
    parser = argparse.ArgumentParser(description="Spike 002: constrained edge fit")
    parser.add_argument("--image", type=str)
    parser.add_argument("--show", action="store_true")
    args = parser.parse_args()

    out_dir = SPIKE_DIR / "output"
    out_dir.mkdir(parents=True, exist_ok=True)
    log = ForensicLog("002-constrained-edge-fit")

    paths = [dataset_dir() / args.image] if args.image else list_dataset()
    results = [run_one(p, out_dir, log, args.show) for p in paths]
    ok_count = sum(1 for r in results if r["ok"])
    summary = {"total": len(results), "fitted": ok_count, "rate": ok_count / max(len(results), 1)}
    log.log("summary", "fit_spike_complete", **summary)
    log.export(out_dir / "forensic.json")
    (out_dir / "results.json").write_text(json.dumps({"summary": summary, "results": results}, indent=2))
    print(json.dumps(summary, indent=2))


if __name__ == "__main__":
    main()

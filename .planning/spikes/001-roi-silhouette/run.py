#!/usr/bin/env python3
"""Spike 001: ROI / silhouette — isolate 3-block cluster from pallet & background."""

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
    draw_roi,
    extract_cluster_roi,
    list_dataset,
    preprocess,
)
from block_detection_v2.edges import detect_edges  # noqa: E402


def run_one(path: Path, out_dir: Path, log: ForensicLog, show: bool) -> dict:
    frame = cv2.imread(str(path))
    if frame is None:
        return {"file": path.name, "ok": False}

    color, gray = preprocess(frame)
    edges, line_count = detect_edges(gray)
    roi = extract_cluster_roi(edges, color.shape[:2], block_mode=3, log=log)

    vis = color.copy()
    ok = roi is not None
    if roi:
        draw_roi(vis, roi)
        cv2.putText(
            vis,
            f"lines={line_count} roi_area={roi.area}",
            (12, vis.shape[0] - 16),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.55,
            (255, 255, 255),
            1,
        )
    else:
        cv2.putText(vis, "ROI FAILED", (12, 40), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 0, 255), 2)

    out_path = out_dir / f"{path.stem}_roi.jpg"
    cv2.imwrite(str(out_path), vis)

    if show:
        cv2.imshow("spike-001-roi", vis)
        cv2.waitKey(0)
        cv2.destroyAllWindows()

    return {
        "file": path.name,
        "ok": ok,
        "lines": line_count,
        "roi": None
        if not roi
        else {"x": int(roi.x), "y": int(roi.y), "w": int(roi.w), "h": int(roi.h), "area": int(roi.area)},
    }


def main() -> None:
    parser = argparse.ArgumentParser(description="Spike 001: ROI silhouette")
    parser.add_argument("--image", type=str, help="Single image name e.g. dt50.jpg")
    parser.add_argument("--show", action="store_true", help="OpenCV window")
    args = parser.parse_args()

    out_dir = SPIKE_DIR / "output"
    out_dir.mkdir(parents=True, exist_ok=True)
    log = ForensicLog("001-roi-silhouette")

    if args.image:
        paths = [dataset_dir() / args.image]
    else:
        paths = list_dataset()

    results = [run_one(p, out_dir, log, args.show) for p in paths]
    ok_count = sum(1 for r in results if r["ok"])
    summary = {
        "total": len(results),
        "roi_found": ok_count,
        "rate": ok_count / max(len(results), 1),
    }
    log.log("summary", "roi_spike_complete", **summary)
    log.export(SPIKE_DIR / "output" / "forensic.json")

    (SPIKE_DIR / "output" / "results.json").write_text(
        json.dumps({"summary": summary, "results": results}, indent=2), encoding="utf-8"
    )
    print(json.dumps(summary, indent=2))


if __name__ == "__main__":
    main()

#!/usr/bin/env python3
"""Offline evaluator scaffold (TEST-02): run detect_block on a labeled image folder."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import cv2

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from block_detected.camera import CaptureFrame  # noqa: E402
from block_detected.detection_contract import DetectionStatus, result_to_dict  # noqa: E402
from block_detected.pipeline import detect_block  # noqa: E402


def main() -> int:
    parser = argparse.ArgumentParser(description="Evaluate detect_block on labeled frames")
    parser.add_argument(
        "image_dir",
        type=Path,
        help="Directory of BGR images (optionally with labels.json sidecar)",
    )
    parser.add_argument("--glob", default="*.png", help="Image glob pattern")
    parser.add_argument("--output", type=Path, help="Write JSON lines report")
    args = parser.parse_args()

    images = sorted(args.image_dir.glob(args.glob))
    if not images:
        print(f"No images matching {args.glob} in {args.image_dir}", file=sys.stderr)
        return 1

    ok = 0
    rows = []
    for path in images:
        bgr = cv2.imread(str(path))
        if bgr is None:
            continue
        if bgr.shape != (480, 640, 3):
            bgr = cv2.resize(bgr, (640, 480))
        capture = CaptureFrame(
            frame_id=path.stem,
            image_bgr=bgr,
            timestamp_ns=0,
            source="eval",
        )
        result = detect_block(capture)
        if result.status == DetectionStatus.OK:
            ok += 1
        rows.append({"image": path.name, "result": result_to_dict(result)})

    summary = {"total": len(rows), "ok": ok, "ok_rate": ok / max(1, len(rows))}
    print(json.dumps(summary, indent=2))
    if args.output:
        args.output.write_text(
            "\n".join(json.dumps(r) for r in rows) + "\n",
            encoding="utf-8",
        )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

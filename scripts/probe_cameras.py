#!/usr/bin/env python3
"""List working camera indices (built-in + USB). Run before picking camera.index."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

_SRC = Path(__file__).resolve().parents[1] / "src"
if str(_SRC) not in sys.path:
    sys.path.insert(0, str(_SRC))

from block_detected.io.camera.probe import format_probe_report, probe_cameras


def main() -> int:
    parser = argparse.ArgumentParser(description="Probe OpenCV camera indices.")
    parser.add_argument(
        "--max-index",
        type=int,
        default=10,
        help="Highest index to scan (default: 10).",
    )
    args = parser.parse_args()
    results = probe_cameras(args.max_index)
    print(format_probe_report(results))
    return 0 if any(r.reads_frames for r in results) else 1


if __name__ == "__main__":
    raise SystemExit(main())

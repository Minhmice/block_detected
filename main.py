#!/usr/bin/env python3
"""Entry point for YOLO webcam inference. Delegates to block_detected package."""

import sys
from pathlib import Path

# Allow running without pip install -e .
_SRC = Path(__file__).resolve().parent / "src"
if str(_SRC) not in sys.path:
    sys.path.insert(0, str(_SRC))

from block_detected.apps.webcam.app import main

if __name__ == "__main__":
    raise SystemExit(main())

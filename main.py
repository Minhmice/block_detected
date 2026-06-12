#!/usr/bin/env python3
"""Launch Block Detected — interactive GUI/TUI picker or direct flags."""

import sys
from pathlib import Path

_SRC = Path(__file__).resolve().parent / "src"
if str(_SRC) not in sys.path:
    sys.path.insert(0, str(_SRC))

from block_detected.apps.launcher import main

if __name__ == "__main__":
    raise SystemExit(main())

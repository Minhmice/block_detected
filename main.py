#!/usr/bin/env python3
"""Launch the Block Detected desktop GUI."""

import sys
from pathlib import Path

_SRC = Path(__file__).resolve().parent / "src"
if str(_SRC) not in sys.path:
    sys.path.insert(0, str(_SRC))

from block_detected.apps.gui.app import main

if __name__ == "__main__":
    raise SystemExit(main())

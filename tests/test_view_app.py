"""Smoke tests for OpenCV view app (no camera)."""

import sys
from pathlib import Path

_ROOT = Path(__file__).resolve().parents[1]
_SRC = _ROOT / "src"
if str(_SRC) not in sys.path:
    sys.path.insert(0, str(_SRC))

from view.app import build_parser, main


def test_view_main_is_callable():
    assert callable(main)


def test_view_parser_accepts_config():
    args = build_parser().parse_args(["--config", "/tmp/cfg.json"])
    assert args.config == Path("/tmp/cfg.json")

"""Main launcher mode resolution (no app startup)."""

import sys
from pathlib import Path

_ROOT = Path(__file__).resolve().parents[1]
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

from main import resolve_mode


def test_resolve_view_flag():
    mode, rest = resolve_mode(["--view"], device="mac")
    assert mode == "view"
    assert rest == []


def test_resolve_gui_alias():
    mode, _rest = resolve_mode(["--gui"], device="mac")
    assert mode == "view"


def test_resolve_tui_flag():
    mode, rest = resolve_mode(["--tui", "--camera-index", "1"], device="mac")
    assert mode == "tui"
    assert rest == ["--camera-index", "1"]


def test_resolve_stream_flag():
    mode, rest = resolve_mode(["--stream", "viewer"], device="mac")
    assert mode == "stream"
    assert rest == ["viewer"]


def test_resolve_target_flag():
    mode, rest = resolve_mode(["--target", "--model", "m.onnx"], device="pi")
    assert mode == "target"
    assert rest == ["--model", "m.onnx"]


def test_resolve_target_positional_mode():
    mode, rest = resolve_mode(["target", "--check-all"], device="pi")
    assert mode == "target"
    assert rest == ["--check-all"]


def test_resolve_positional_mode():
    mode, _rest = resolve_mode(["tui"], device="mac")
    assert mode == "tui"


def test_resolve_env_mode(monkeypatch):
    monkeypatch.setenv("BLOCK_DETECTED_UI", "tui")
    mode, _rest = resolve_mode([], device="mac")
    assert mode == "tui"

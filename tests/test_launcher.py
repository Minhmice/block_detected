"""Launcher mode resolution (no GUI/TUI startup)."""

import pytest

from block_detected.apps.launcher import resolve_mode


def test_resolve_gui_flag():
    mode, rest = resolve_mode(["--gui"])
    assert mode == "gui"
    assert rest == []


def test_resolve_tui_flag():
    mode, rest = resolve_mode(["--tui", "--camera-index", "1"])
    assert mode == "tui"
    assert rest == ["--camera-index", "1"]


def test_resolve_positional_mode():
    mode, _rest = resolve_mode(["tui"])
    assert mode == "tui"


def test_resolve_env_mode(monkeypatch):
    monkeypatch.setenv("BLOCK_DETECTED_UI", "gui")
    mode, _rest = resolve_mode([])
    assert mode == "gui"


def test_resolve_rejects_both_flags():
    mode, _rest = resolve_mode(["--gui", "--tui"])
    assert mode == "quit"

"""Entry launcher — pick GUI or TUI when starting from a terminal."""

from __future__ import annotations

import os
import sys


def _print_picker() -> None:
    print()
    print("  Block Detected — chọn giao diện")
    print()
    print("    1  GUI   Desktop PySide6 (preview camera + controls)")
    print("    2  TUI   Textual dashboard (metrics trong terminal)")
    print()
    print("    q  Thoát")
    print()


def prompt_ui_mode() -> str:
    """Return ``gui``, ``tui``, or ``quit``."""
    _print_picker()
    while True:
        try:
            choice = input("Chọn [1/2/q] (mặc định 1): ").strip().lower()
        except (EOFError, KeyboardInterrupt):
            print()
            return "quit"
        if choice in ("", "1", "gui", "g"):
            return "gui"
        if choice in ("2", "tui", "t"):
            return "tui"
        if choice in ("q", "quit", "exit"):
            return "quit"
        print("Nhập 1, 2 hoặc q.")


def _strip_launcher_flags(argv: list[str]) -> tuple[bool, bool, list[str]]:
    """Return (want_gui, want_tui, remaining argv for sub-apps)."""
    want_gui = False
    want_tui = False
    rest: list[str] = []
    for token in argv:
        if token in ("--gui", "-g"):
            want_gui = True
            continue
        if token in ("--tui", "-t"):
            want_tui = True
            continue
        if token in ("--help", "-h"):
            continue
        rest.append(token)
    return want_gui, want_tui, rest


def resolve_mode(argv: list[str]) -> tuple[str, list[str]]:
    """Parse launcher flags and return (mode, remaining_args_for_subapp)."""
    argv = list(argv)
    if argv[:1] == ["--help"] or argv[:1] == ["-h"]:
        _print_launcher_help()
        return "quit", []

    want_gui, want_tui, rest = _strip_launcher_flags(argv)

    if argv and argv[0] in ("gui", "tui"):
        mode_token = argv[0]
        rest = argv[1:]
        want_gui = mode_token == "gui"
        want_tui = mode_token == "tui"

    if want_gui and want_tui:
        print("[ERROR] Chỉ chọn một trong --gui và --tui.")
        return "quit", rest

    if want_gui:
        return "gui", rest
    if want_tui:
        return "tui", rest

    env_mode = os.environ.get("BLOCK_DETECTED_UI", "").strip().lower()
    if env_mode in ("gui", "tui"):
        return env_mode, rest

    if sys.stdin.isatty() and sys.stdout.isatty():
        picked = prompt_ui_mode()
        if picked == "quit":
            return "quit", rest
        return picked, rest

    _print_launcher_help()
    return "quit", rest


def _print_launcher_help() -> None:
    print("usage: block-detected [--gui | --tui] [tui options...]")
    print()
    print("YOLO webcam detection — GUI desktop hoặc TUI terminal.")
    print()
    print("options:")
    print("  --gui, -g     PySide6 desktop (preview + controls)")
    print("  --tui, -t     Textual dashboard (metrics trong terminal)")
    print("  gui | tui     Chọn giao diện (positional)")
    print()
    print("Gợi ý: python main.py --gui   hoặc   python main.py --tui --camera-index 1")
    print("       export BLOCK_DETECTED_UI=tui")


def _missing_extra_message(extra: str, packages: str) -> int:
    print(f"[ERROR] Missing optional dependency for [{extra}]: {packages}")
    print(f'[INFO] Install with: pip install -e ".[{extra}]"')
    return 1


def run_gui() -> int:
    try:
        import PySide6  # noqa: F401
    except ModuleNotFoundError:
        return _missing_extra_message("gui", "PySide6")
    from block_detected.apps.gui.app import main as gui_main

    return gui_main()


def run_tui(argv: list[str]) -> int:
    try:
        import rich  # noqa: F401
        import textual  # noqa: F401
    except ModuleNotFoundError:
        return _missing_extra_message("tui", "textual, rich")
    from block_detected.apps.tui.app import main as tui_main

    return tui_main(argv)


def main(argv: list[str] | None = None) -> int:
    argv = list(sys.argv[1:] if argv is None else argv)
    mode, rest = resolve_mode(argv)
    if mode == "quit":
        return 0
    if mode == "gui":
        return run_gui()
    return run_tui(rest)


if __name__ == "__main__":
    raise SystemExit(main())

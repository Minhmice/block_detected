#!/usr/bin/env python3
"""Launch Block Detected — bootstrap, device-aware picker, stream/view/tui."""

from __future__ import annotations

import os
import sys
from pathlib import Path

from bootstrap import (
    DeviceKind,
    default_mode,
    detect_device,
    ensure_environment,
    prompt_mode,
    warn_pi_view,
)

_SRC = Path(__file__).resolve().parent / "src"
if str(_SRC) not in sys.path:
    sys.path.insert(0, str(_SRC))


def _strip_mode_flags(argv: list[str]) -> tuple[str | None, list[str]]:
    mode: str | None = None
    rest: list[str] = []
    for token in argv:
        if token in ("--stream", "-s"):
            mode = "stream"
            continue
        if token in ("--view", "-v", "--gui", "-g"):
            mode = "view"
            continue
        if token in ("--tui", "-t"):
            mode = "tui"
            continue
        if token in ("--help", "-h"):
            continue
        rest.append(token)
    return mode, rest


def resolve_mode(
    argv: list[str],
    *,
    device: DeviceKind | None = None,
) -> tuple[str, list[str]]:
    if argv[:1] in (["--help"], ["-h"]):
        _print_help()
        return "quit", []

    device = device or detect_device()
    mode, rest = _strip_mode_flags(argv)

    if argv and argv[0] in ("stream", "view", "tui", "gui"):
        token = "view" if argv[0] == "gui" else argv[0]
        extra = argv[1:]
        if device == "pi" and token == "view":
            warn_pi_view()
        return token, extra

    if mode is not None:
        if device == "pi" and mode == "view":
            warn_pi_view()
        return mode, rest

    env_mode = os.environ.get("BLOCK_DETECTED_UI", "").strip().lower()
    if env_mode in ("stream", "view", "tui", "gui"):
        picked = "view" if env_mode == "gui" else env_mode
        if device == "pi" and picked == "view":
            warn_pi_view()
        return picked, rest

    if sys.stdin.isatty() and sys.stdout.isatty():
        picked, picker_rest = prompt_mode(device)
        if picked == "quit":
            return "quit", rest
        return picked, picker_rest + rest

    return default_mode(device), rest


def _print_help() -> None:
    print("usage: python main.py [--stream | --view | --tui] [app options...]")
    print()
    print("  --stream, -s       Pi JPEG stream server")
    print("  --view, -v         OpenCV detection preview (desktop)")
    print("  --tui, -t          Textual detection dashboard")
    print("  --probe-cameras    List working camera indices (USB / built-in)")
    print("  --no-install       Skip auto pip install")
    print("  --install          Force reinstall profile deps")
    print("  --install-pi       Pi 5 deps only (no CUDA from core/all extras)")
    print()
    print("  stream viewer:     python main.py --stream viewer")
    print("  config file:       src/block_detected/block_detected.json")


def _missing_extra(extra: str, packages: str) -> int:
    print(f"[ERROR] Missing optional dependency for [{extra}]: {packages}")
    print(f'[INFO] Install with: pip install -e ".[{extra}]"')
    return 1


def main(argv: list[str] | None = None) -> int:
    argv = list(sys.argv[1:] if argv is None else argv)
    if argv[:1] == ["--probe-cameras"]:
        from block_detected.io.camera.probe import format_probe_report, probe_cameras

        max_index = 10
        if len(argv) >= 2 and argv[1].isdigit():
            max_index = int(argv[1])
        print(format_probe_report(probe_cameras(max_index)))
        return 0

    device, argv = ensure_environment(argv)
    mode, rest = resolve_mode(argv, device=device)
    if mode == "quit":
        return 0

    if mode == "stream":
        from stream.__main__ import main as stream_main

        return stream_main(rest)

    if mode == "view":
        try:
            import cv2  # noqa: F401
            if not hasattr(cv2, "imshow"):
                raise ImportError("opencv headless")
        except ImportError:
            return _missing_extra("view", "opencv-python")
        from view.app import main as view_main

        return view_main(rest)

    try:
        import rich  # noqa: F401
        import textual  # noqa: F401
    except ModuleNotFoundError:
        return _missing_extra("tui", "textual, rich")
    from block_detected.tui.app import main as tui_main

    return tui_main(rest)


if __name__ == "__main__":
    raise SystemExit(main())

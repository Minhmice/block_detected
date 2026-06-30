"""Bootstrap: device detection, dependency check, and auto-install."""

from __future__ import annotations

import importlib
import importlib.util
import os
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Literal

DeviceKind = Literal["pi", "mac", "windows", "linux"]

REPO_ROOT = Path(__file__).resolve().parent
SRC_ROOT = REPO_ROOT / "src"

CORE_MODULES = ("ultralytics", "cv2", "rich", "textual")
LAUNCHER_FLAGS = frozenset({"--no-install", "--install", "--help", "-h"})


@dataclass(frozen=True, slots=True)
class EnvironmentStatus:
    in_venv: bool
    missing_modules: tuple[str, ...]
    package_installed: bool
    view_ready: bool


def _read_first_line(path: Path) -> str:
    try:
        return path.read_text(encoding="utf-8", errors="replace").strip()
    except OSError:
        return ""


def _is_raspberry_pi() -> bool:
    if not sys.platform.startswith("linux"):
        return False
    model = _read_first_line(Path("/proc/device-tree/model"))
    if "Raspberry Pi" in model:
        return True
    cpuinfo = _read_first_line(Path("/proc/cpuinfo"))
    return "BCM" in cpuinfo


def detect_device() -> DeviceKind:
    if _is_raspberry_pi():
        return "pi"
    if sys.platform == "darwin":
        return "mac"
    if sys.platform == "win32":
        return "windows"
    return "linux"


def device_label(device: DeviceKind) -> str:
    return {
        "pi": "Raspberry Pi",
        "mac": "macOS",
        "windows": "Windows",
        "linux": "Linux",
    }[device]


def profile_label(device: DeviceKind) -> str:
    return "pi-lite" if device == "pi" else "desktop-view"


def is_in_venv() -> bool:
    return sys.prefix != sys.base_prefix or bool(os.environ.get("VIRTUAL_ENV"))


def _has_module(name: str) -> bool:
    return importlib.util.find_spec(name) is not None


def _view_ready() -> bool:
    if not _has_module("cv2"):
        return False
    import cv2

    return hasattr(cv2, "imshow")


def check_environment() -> EnvironmentStatus:
    missing = tuple(mod for mod in CORE_MODULES if not _has_module(mod))
    package_installed = _has_module("block_detected")
    return EnvironmentStatus(
        in_venv=is_in_venv(),
        missing_modules=missing,
        package_installed=package_installed,
        view_ready=_view_ready(),
    )


def needs_install(status: EnvironmentStatus, device: DeviceKind, *, force: bool = False) -> bool:
    if force:
        return True
    if status.missing_modules or not status.package_installed:
        return True
    if device != "pi" and not status.view_ready:
        return True
    return False


def _run_pip(args: list[str]) -> bool:
    cmd = [sys.executable, "-m", "pip", *args]
    print(f"[INFO] Running: {' '.join(cmd)}")
    result = subprocess.run(cmd, cwd=REPO_ROOT, check=False)
    if result.returncode != 0:
        print(f"[ERROR] pip failed (exit {result.returncode})")
        return False
    return True


def install_profile(device: DeviceKind) -> bool:
    if device == "pi":
        ok = _run_pip(["install", "-r", "requirements-pi.txt"])
        if not ok:
            return False
        return _run_pip(["install", "-e", ".", "--no-deps"])
    return _run_pip(["install", "-e", ".[view]"])


def strip_launcher_flags(argv: list[str]) -> tuple[list[str], bool, bool]:
    """Return (rest, no_install, force_install)."""
    no_install = False
    force_install = False
    rest: list[str] = []
    for token in argv:
        if token == "--no-install":
            no_install = True
            continue
        if token == "--install":
            force_install = True
            continue
        rest.append(token)
    return rest, no_install, force_install


def ensure_environment(argv: list[str]) -> tuple[DeviceKind, list[str]]:
    device = detect_device()
    argv, no_install, force_install = strip_launcher_flags(argv)

    print(f"[INFO] Device: {device_label(device)}")
    print(f"[INFO] Profile: {profile_label(device)}")
    if not is_in_venv():
        print("[WARN] Not running inside a virtualenv — install may affect system Python.")

    status = check_environment()
    if no_install:
        if needs_install(status, device):
            print("[WARN] Dependencies incomplete (--no-install). Apps may fail to start.")
        return device, argv

    if needs_install(status, device, force=force_install):
        if status.missing_modules:
            print(f"[INFO] Missing modules: {', '.join(status.missing_modules)}")
        if not status.package_installed:
            print("[INFO] Package block_detected not installed.")
        if device != "pi" and not status.view_ready:
            print("[INFO] OpenCV HighGUI not available (desktop view).")
        if not install_profile(device):
            print("[ERROR] Auto-install failed. Try manually:")
            if device == "pi":
                print("  pip install -r requirements-pi.txt && pip install -e . --no-deps")
            else:
                print('  pip install -e ".[view]"')
        else:
            importlib.invalidate_caches()
            print("[INFO] Install complete.")

    return device, argv


def default_mode(device: DeviceKind) -> str:
    return "tui" if device == "pi" else "view"


def print_picker(device: DeviceKind) -> None:
    print()
    if device == "pi":
        print(f"  Block Detected — {device_label(device)}")
        print()
        print("    1  Stream   JPEG server (TCP/UDP)")
        print("    2  TUI      Detection dashboard   [mặc định]")
        print()
        print("    q  Thoát")
    else:
        print(f"  Block Detected — {device_label(device)}")
        print()
        print("    1  View     OpenCV + YOLO           [mặc định]")
        print("    2  TUI      Terminal dashboard")
        print("    3  Stream   LAN viewer (xem Pi)")
        print()
        print("    q  Thoát")
    print()


def prompt_mode(device: DeviceKind) -> tuple[str, list[str]]:
    print_picker(device)
    default = default_mode(device)
    if device == "pi":
        hint = "Chọn [1/2/q] (mặc định 2): "
    else:
        hint = "Chọn [1/2/3/q] (mặc định 1): "
    while True:
        try:
            choice = input(hint).strip().lower()
        except (EOFError, KeyboardInterrupt):
            print()
            return "quit", []
        if device == "pi":
            if choice in ("", "2", "tui", "t"):
                return "tui", []
            if choice in ("1", "stream", "s"):
                return "stream", []
            if choice in ("q", "quit", "exit"):
                return "quit", []
            print("Nhập 1, 2 hoặc q.")
            continue
        if choice in ("", "1", "view", "v"):
            return "view", []
        if choice in ("2", "tui", "t"):
            return "tui", []
        if choice in ("3", "stream", "s"):
            return "stream", ["viewer"]
        if choice in ("q", "quit", "exit"):
            return "quit", []
        print("Nhập 1, 2, 3 hoặc q.")


def warn_pi_view() -> None:
    print(
        "[WARN] View cần opencv-python (HighGUI) — không khuyến nghị trên Pi. "
        "Dùng TUI hoặc Stream."
    )

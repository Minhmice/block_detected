"""Bootstrap launcher: device detection, install, picker."""

from __future__ import annotations

import sys
from pathlib import Path
from unittest.mock import MagicMock, patch

_ROOT = Path(__file__).resolve().parents[1]
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

import bootstrap
from main import resolve_mode


def test_detect_pi(monkeypatch, tmp_path):
    model = tmp_path / "model"
    model.write_text("Raspberry Pi 4 Model B Rev 1.4\x00", encoding="utf-8")

    def fake_read(path):
        if str(path) == "/proc/device-tree/model":
            return model.read_text(encoding="utf-8").strip()
        return ""

    monkeypatch.setattr(bootstrap, "_read_first_line", fake_read)
    monkeypatch.setattr(sys, "platform", "linux")
    assert bootstrap.detect_device() == "pi"


def test_detect_mac(monkeypatch):
    monkeypatch.setattr(bootstrap, "_is_raspberry_pi", lambda: False)
    monkeypatch.setattr(sys, "platform", "darwin")
    assert bootstrap.detect_device() == "mac"


def test_desktop_picker_default(monkeypatch):
    monkeypatch.setattr(bootstrap, "_is_raspberry_pi", lambda: False)
    monkeypatch.setattr(sys, "platform", "darwin")
    monkeypatch.setattr(sys.stdin, "isatty", lambda: True)
    monkeypatch.setattr(sys.stdout, "isatty", lambda: True)
    monkeypatch.setattr("builtins.input", lambda _hint: "")
    mode, rest = resolve_mode([], device="mac")
    assert mode == "view"
    assert rest == []


def test_pi_picker_default(monkeypatch):
    monkeypatch.setattr(sys.stdin, "isatty", lambda: True)
    monkeypatch.setattr(sys.stdout, "isatty", lambda: True)
    monkeypatch.setattr("builtins.input", lambda _hint: "")
    mode, rest = resolve_mode([], device="pi")
    assert mode == "tui"
    assert rest == []


def test_non_tty_defaults(monkeypatch):
    monkeypatch.setattr(sys.stdin, "isatty", lambda: False)
    monkeypatch.setattr(sys.stdout, "isatty", lambda: False)
    mode, _rest = resolve_mode([], device="mac")
    assert mode == "view"
    mode, _rest = resolve_mode([], device="pi")
    assert mode == "tui"


def test_install_skipped_with_flag(monkeypatch):
    calls: list[list[str]] = []

    def fake_run(cmd, cwd, check):  # noqa: ARG001
        calls.append(cmd)
        return MagicMock(returncode=0)

    monkeypatch.setattr(bootstrap.subprocess, "run", fake_run)
    monkeypatch.setattr(bootstrap, "check_environment", lambda: bootstrap.EnvironmentStatus(
        in_venv=True,
        missing_modules=("ultralytics",),
        package_installed=False,
        view_ready=False,
    ))
    device, rest = bootstrap.ensure_environment(["--no-install", "--view"])
    assert device in ("mac", "linux", "windows", "pi")
    assert rest == ["--view"]
    assert calls == []


def test_install_pi_profile(monkeypatch):
    calls: list[list[str]] = []

    def fake_run(cmd, cwd, check):  # noqa: ARG001
        calls.append(cmd)
        return MagicMock(returncode=0)

    monkeypatch.setattr(bootstrap.subprocess, "run", fake_run)
    monkeypatch.setattr(bootstrap, "detect_device", lambda: "pi")
    monkeypatch.setattr(bootstrap, "check_environment", lambda: bootstrap.EnvironmentStatus(
        in_venv=True,
        missing_modules=("ultralytics",),
        package_installed=False,
        view_ready=False,
    ))
    with patch.object(bootstrap.importlib, "invalidate_caches"):
        bootstrap.ensure_environment([])
    assert len(calls) == 2
    assert calls[0][-2:] == ["-r", "requirements-pi.txt"]
    assert calls[1][-3:] == ["-e", ".", "--no-deps"]


def test_install_desktop_profile(monkeypatch):
    calls: list[list[str]] = []

    def fake_run(cmd, cwd, check):  # noqa: ARG001
        calls.append(cmd)
        return MagicMock(returncode=0)

    monkeypatch.setattr(bootstrap.subprocess, "run", fake_run)
    monkeypatch.setattr(bootstrap, "detect_device", lambda: "mac")
    monkeypatch.setattr(bootstrap, "check_environment", lambda: bootstrap.EnvironmentStatus(
        in_venv=True,
        missing_modules=(),
        package_installed=True,
        view_ready=False,
    ))
    with patch.object(bootstrap.importlib, "invalidate_caches"):
        bootstrap.ensure_environment([])
    assert len(calls) == 1
    assert calls[0][-1] == ".[view]"


def test_device_kind_platform():
    _src = _ROOT / "src"
    if str(_src) not in sys.path:
        sys.path.insert(0, str(_src))
    from block_detected.runtime.platform import device_kind

    assert device_kind() in ("pi", "mac", "windows", "linux")

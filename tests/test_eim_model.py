"""Tests for EIM model path validation."""

from __future__ import annotations

from pathlib import Path

import pytest

from app.services.eim_model import (
    is_vision_mock_mode,
    resolve_eim_path,
    validate_eim_model,
)


def test_validate_missing_model(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    missing = tmp_path / "missing.eim"
    monkeypatch.setenv("EI_MODEL_PATH", str(missing))
    status = validate_eim_model()
    assert status.exists is False
    assert status.executable is False
    assert status.error is not None
    assert "not found" in status.error


def test_validate_not_executable(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    model = tmp_path / "model.eim"
    model.write_text("fake", encoding="utf-8")
    model.chmod(0o644)
    monkeypatch.setenv("EI_MODEL_PATH", str(model))
    status = validate_eim_model()
    assert status.exists is True
    assert status.executable is False
    assert status.error is not None
    assert "chmod +x" in status.error


def test_validate_executable(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    model = tmp_path / "model.eim"
    model.write_text("fake", encoding="utf-8")
    model.chmod(0o755)
    monkeypatch.setenv("EI_MODEL_PATH", str(model))
    status = validate_eim_model()
    assert status.executable is True
    assert status.error is None


def test_is_vision_mock_mode_default_true(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("VISION_MOCK_MODE", raising=False)
    assert is_vision_mock_mode() is True


def test_is_vision_mock_mode_false(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("VISION_MOCK_MODE", "false")
    assert is_vision_mock_mode() is False


def test_resolve_eim_path_from_registry_default(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("EI_MODEL_PATH", raising=False)
    monkeypatch.delenv("EI_MODEL_ID", raising=False)
    path = resolve_eim_path()
    assert path.name == "shit-linux-aarch64-v1-impulse-#1.eim"

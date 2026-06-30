"""Tests for default dependency layout in pyproject.toml."""

from pathlib import Path

import tomllib


def _load_pyproject() -> dict:
    path = Path(__file__).resolve().parents[1] / "pyproject.toml"
    return tomllib.loads(path.read_text(encoding="utf-8"))


def test_default_deps_no_pyside6():
    data = _load_pyproject()
    core = data["project"]["dependencies"]
    optional = data["project"]["optional-dependencies"]

    assert any("ultralytics" in d for d in core)
    assert any("opencv-python-headless" in d for d in core)
    assert not any("PySide6" in d for d in core)
    assert any("textual" in d for d in core)
    assert any("rich" in d for d in core)
    assert "view" in optional
    assert "viewer" in optional
    assert "stream" in optional
    assert "all" in optional
    assert "dev" in optional


def test_requirements_pi_excludes_pyside6():
    path = Path(__file__).resolve().parents[1] / "requirements-pi.txt"
    dep_lines = [
        line.strip().lower()
        for line in path.read_text(encoding="utf-8").splitlines()
        if line.strip() and not line.strip().startswith("#")
    ]
    assert not any("pyside6" in line for line in dep_lines)
    assert any("ultralytics" in line for line in dep_lines)
    assert any("textual" in line for line in dep_lines)

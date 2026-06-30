# Testing (quality-focused)

**Analysis Date:** 2026-06-30

This repo’s tests are designed to be **fast, hardware-free, and deterministic**. The suite heavily prefers **fake detectors/caps** and “pure” helpers over opening cameras or loading real weights.

## How to Run

- **Install test dependencies** (pytest is optional extra `dev`)  
  Evidence: `pyproject.toml` → `[project.optional-dependencies] dev = ["pytest>=8.0", "httpx>=0.27"]`

```bash
pip install -e ".[dev]"
python -m pytest tests/ -q
```

- **Run a single file**:

```bash
python -m pytest tests/test_tui_app.py -q
```

- **Collect-only**:

```bash
python -m pytest tests/ -q --collect-only
```

## What the Suite Assumes (dependencies)

- **Core runtime dependencies** are required for engine-related imports  
  Evidence: `pyproject.toml` base `dependencies` include `ultralytics`, `opencv-python-headless`, `textual`, `rich`
- **TUI tests** skip cleanly if `rich`/`textual` are missing  
  Evidence: `tests/test_tui_app.py` uses `pytest.importorskip("rich")` and `pytest.importorskip("textual")`

## Where Tests Live

- **All tests are under `tests/`** (not co-located with source)  
  Evidence: repo structure and the directory itself
- **Import bootstrap lives in `tests/conftest.py`**  
  Evidence: `tests/conftest.py` inserts both `src/` and repo root into `sys.path`

## What’s Covered (representative)

- **Launcher/bootstrap behavior** (device detection, install profiles, non-TTY defaults)  
  Evidence: `tests/test_bootstrap.py`, `tests/test_launcher.py`
- **TUI behaviors** (argument parsing, rendering helpers, runtime wrapper with fake engine)  
  Evidence: `tests/test_tui_app.py`
- **OpenCV view app smoke** (parser + entrypoint callability; no camera)  
  Evidence: `tests/test_view_app.py`
- **Config/layout guarantees** (dependency extras, pi requirements)  
  Evidence: `tests/test_deps_layout.py`
- **Engine loop logic without hardware** (fake cap + fake detector; postprocess integration)  
  Evidence: `tests/test_engine_process.py`

## Test Design Conventions (to preserve)

- **No real cameras** and **no real model weights** in tests  
  Evidence: engine tests inject fake components (e.g. `tests/test_engine_process.py`)
- **Prefer fakes over heavyweight mocks** for domain/runtime behavior  
  Evidence: `_FakeCap`, `_FakeDetector` patterns in `tests/test_engine_process.py`
- **Use `try_*` return tuples**, assert on `(ok, error)` or `(value, error)` rather than expecting exceptions  
  Evidence: `tests/test_engine_create.py`, engine APIs in `src/block_detected/runtime/engine.py`

## Mocking & Patching

- **pytest `monkeypatch` is common**, but `unittest.mock` is also used when convenient  
  Evidence:
  - `tests/test_bootstrap.py` uses `from unittest.mock import MagicMock, patch`
  - many engine tests use `monkeypatch` fixtures (see `tests/test_engine_process.py`)

## Optional GUI Notes

- **No PySide6 GUI tests are present in `tests/` in this repo snapshot** (despite optional GUI code existing under `src/block_detected/apps/`), so keep GUI-related work covered via import/smoke tests if added later.

## Gaps / Future Improvements (when touching related areas)

- **CI**: no GitHub Actions workflows detected under `.github/workflows/` in this snapshot (directory absent). Consider adding CI only if/when you need automated checks.
- **Coverage**: no coverage tooling/config is present. If adding, prefer `pytest-cov` and keep gates modest to avoid slowing iteration.

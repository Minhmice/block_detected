# Conventions (quality-focused)

**Analysis Date:** 2026-06-30

This doc captures conventions that matter for maintainability: module layout, imports, typing, error-handling, logging, configuration, and “don’t break the layering”.

## Repository Layout (what goes where)

- **`src/block_detected/`**: primary library + runtime pipeline + config + TUI entrypoints  
  Evidence: `src/block_detected/runtime/engine.py`, `src/block_detected/runtime/logging_setup.py`
- **`src/view/`**: OpenCV view app (desktop)  
  Evidence: `pyproject.toml` scripts include `block-detected-view = "view.app:main"`, plus `tests/test_view_app.py`
- **`src/stream/`**: Pi stream server + LAN viewer (standalone; no `block_detected` import)  
  Evidence: `AGENTS.md` dependency rules
- **Repo-root scripts**: launcher + bootstrap are repo-root modules (not in `src/`)  
  Evidence: `main.py`, `bootstrap.py`, and `pyproject.toml` has `py-modules = ["main", "bootstrap"]`
- **Experimental/legacy**: `src/block_detection_v2/` exists and has benchmark output; treat as non-critical unless you’re actively working there  
  Evidence: `.gitignore` ignores `src/block_detection_v2/benchmark_output/`

## Naming & API Patterns

- **Files/modules**: `snake_case.py` throughout  
  Evidence: `src/block_detected/runtime/logging_setup.py`, `src/block_detected/detection/yolo/loader.py`
- **Classes**: `PascalCase` for core types and engines  
  Evidence: `WebcamEngine`, `ProcessedFrame` in `src/block_detected/runtime/engine.py`
- **Public “soft failure” APIs**: prefer `try_*` methods that return `(value | None, error | None)` / `(ok: bool, error | None)`  
  Evidence: `WebcamEngine.try_create()` and `WebcamEngine.try_start()` in `src/block_detected/runtime/engine.py`
- **Private state**: private fields prefixed with `_`  
  Evidence: `WebcamEngine._detector`, `WebcamEngine._cap` in `src/block_detected/runtime/engine.py`

## Python Version, Typing, and Modern Syntax

- **Python baseline**: 3.10+  
  Evidence: `pyproject.toml` → `requires-python = ">=3.10"`
- **Annotations**: use `from __future__ import annotations` when forward types appear  
  Evidence: `main.py`, `bootstrap.py`, `src/block_detected/runtime/engine.py`, `src/block_detected/runtime/logging_setup.py`
- **Union syntax**: use modern unions (`X | None`)  
  Evidence: `WebcamEngine.try_create(...) -> tuple[WebcamEngine | None, str | None]` (`src/block_detected/runtime/engine.py`)
- **Use `Any` sparingly** for third‑party payloads where practical typing is noisy  
  Evidence: `ProcessedFrame.annotated: Any` in `src/block_detected/runtime/engine.py`

## Imports & Dependency Boundaries

- **Prefer absolute imports** (`from block_detected...`) for library code  
  Evidence: `src/block_detected/runtime/engine.py`
- **Keep bootstrapping hacks local**: path injection is OK in launchers/tests, not in library modules  
  Evidence: `main.py` inserts `src/` into `sys.path`; `tests/conftest.py` inserts `src/` and repo root
- **Optional dependency strategy**: keep “view window” requirements optional by checking `cv2.imshow` availability  
  Evidence: `main.py` checks `hasattr(cv2, "imshow")` and otherwise prints install guidance for `.[view]`

## Error Handling

- **Recoverable startup failures return tuples** and log a clear message at the failure site  
  Evidence: `WebcamEngine.try_create()` returns `(None, message)` and logs (`src/block_detected/runtime/engine.py`)
- **Non-fatal cleanup errors should warn, not crash**  
  Evidence: model switch close failure logs `logger.warning(...)` (`src/block_detected/runtime/engine.py`)

## Logging (baseline)

- **Standard library `logging` only**, with a ring-buffer handler for UI/TUI consumption  
  Evidence: `src/block_detected/runtime/logging_setup.py` (`LogBufferHandler`, `setup_logging`, `get_log_lines`, `log_event`)
- **Centralize setup** in `setup_logging(...)`, avoid bespoke handlers in modules  
  Evidence: `src/block_detected/runtime/logging_setup.py`
- **Reduce noisy third-party logs explicitly**  
  Evidence: `logging.getLogger("ultralytics").setLevel(logging.WARNING)` in `src/block_detected/runtime/logging_setup.py`

## Configuration & Persistence

- **Primary detection config is JSON** under `src/block_detected/`  
  Evidence: `README.md` references `src/block_detected/block_detected.json`
- **Persist user-facing config updates** via the config store  
  Evidence: `src/block_detected/runtime/engine.py` calls `save_config(...)` after switching model
- **Avoid new wildcard re-export modules**: `src/block_detected/runtime/config_schema.py` is explicitly marked “deprecated path” and should not be copied as a pattern  
  Evidence: docstring + `from ... import *` in `src/block_detected/runtime/config_schema.py`

## Files and Artifacts: what must not be committed

- **Do not commit large weights / ML artifacts**  
  Evidence: `.gitignore` ignores `models/*.pt` and `runs/`, `wandb/`
- **Do not commit accidental venv copies**  
  Evidence: `.gitignore` ignores `Lib/`, `Scripts/`, `Include/` and states “never commit site-packages”
- **Tool caches**  
  Evidence: `.gitignore` ignores `.pytest_cache/`, `.mypy_cache/`, `.ruff_cache/`

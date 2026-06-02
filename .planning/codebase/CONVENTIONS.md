# Coding Conventions

**Analysis Date:** 2026-06-02

## Naming Patterns

**Files:**
- Snake_case Python modules: `app.py`, `capture.py`, `loader.py`
- Package `__init__.py` files re-export public API where present (`config/__init__.py`, `detection/__init__.py`)
- Tests named `test_<area>.py` under `tests/`

**Functions:**
- snake_case with verb prefixes: `open_camera`, `switch_camera`, `discover_model_paths`, `extract_boxes`, `draw_eval_boxes`
- Private test helpers prefixed with `_`: `_FakeResult`, `_FakeBox` in `tests/test_boxes.py`

**Variables:**
- snake_case: `model_paths`, `current_boxes`, `overlay_enabled`, `ui_state`
- Constants UPPER_SNAKE in config modules: `DEFAULT_CONF`, `MODELS_DIR`, `WINDOW_NAME`

**Types:**
- PascalCase aliases when used: `Box` as `TypeAlias` in `core/types.py`
- Modern union syntax: `str | Path`, `cv2.VideoCapture | None` in `io/images/__init__.py`, `io/camera/capture.py`

## Code Style

**Formatting:**
- No formatter or linter config in repo (no `ruff.toml`, `[tool.ruff]`, `black`, or `.flake8`)
- `.gitignore` anticipates `.ruff_cache/` and `.mypy_cache/` but tools are not configured
- Observed style: 4-space indent, double quotes for strings, trailing commas in multi-line imports

**Linting:**
- Not configured — rely on manual review and pytest

**Type hints:**
- Used on public functions in newer modules (`extract_boxes`, `handle_key`, `iter_image_paths`, `open_camera`)
- Not exhaustive across every function (e.g. `extract_boxes(result)` untyped parameter for Ultralytics result)

## Import Organization

**Order:**
1. Standard library (`collections`, `pathlib`, `sys`, `typing`)
2. Third party (`cv2`, `ultralytics` only in detection layer)
3. `block_detected.*` submodules — prefer direct submodule imports per `AGENTS.md`

**Path Aliases:**
- Package name `block_detected` (src layout via setuptools `where = ["src"]`)
- No `src.` prefix in imports after install or `conftest`/`main.py` path setup

**Barrel imports:**
- Apps may import from `block_detected.config` barrel (`apps/webcam/app.py`)
- Prefer `from block_detected.vision.geometry import point_in_rect` over star imports
- Keep root `block_detected/__init__.py` free of OpenCV/YOLO imports (`AGENTS.md`)

## Error Handling

**Patterns:**
- Early return with exit code from `main()` for setup failures (no models, camera, initial load)
- try/except around model load and per-frame inference with user-visible `print` messages
- `finally` for resource cleanup (`cap.release()`, `cv2.destroyAllWindows()`)
- Do not swallow exceptions silently — log and break or return non-zero

**When adding code:**
- Use same `[INFO|WARN|ERROR]` print prefix until a logging module exists
- Return `int` from app `main()` for CLI exit status

## Logging

**Framework:** stdout `print` only

**Patterns:**
- Tag: `[INFO]`, `[WARN]`, `[ERROR]` at start of message
- Log state changes users care about (model switch, conf change, mode toggles) in `handlers.py` and `app.py`
- Avoid logging every frame

## Comments

**When to Comment:**
- Module docstrings at top of files (`"""Webcam inference application..."""`)
- Stub packages document future intent (`apps/batch/__init__.py`, `io/images/__init__.py`)
- Avoid narrating obvious code; `AGENTS.md` holds architectural guidance

**Docstrings:**
- Use for public functions with non-obvious return shapes (`handle_key`, `switch_camera`, `iter_image_paths`)
- Return tuple documented in `handle_key` docstring

## Function Design

**Size:**
- Keep `apps/*/app.py` as orchestration — delegate drawing to `vision/drawing`, input to `ui/input`
- Single-purpose functions in `io/` and `detection/` (one concern per function)

**Parameters:**
- Use keyword-only args after `*` where API has multiple flags (`handle_key`)
- Pass callbacks via `ui_state` dict for mouse handler (`switch_model`)

**Return Values:**
- App `main() -> int` for exit codes
- Pure helpers return domain values (`list[Box]`, `list[Path]`, `bool` for hit tests)

## Module Design

**Exports:**
- Subpackage `__init__.py` re-exports stable surface (`detection/__init__.py` → `extract_boxes`)
- Config barrel aggregates constants for app convenience

**Barrel Files:**
- `config/__init__.py` — yes, for app imports
- Do not create a heavy top-level `block_detected` API that imports cv2/YOLO

**Dependency rules (mandatory):**
- `detection` must not import `apps` or `ui`
- `vision` must not import `detection`
- `core` must not import OpenCV or Ultralytics

## Config Conventions

- All filesystem paths via `config/paths.py` — compute `PROJECT_ROOT` from `Path(__file__).resolve().parents[3]`
- Never name a package subfolder `models/` (conflicts with repo `models/*.pt`)
- Default model filename only in `config/inference.py` (`DEFAULT_MODEL_NAME`)

---

*Convention analysis: 2026-06-02*

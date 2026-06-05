# Technology Stack

**Analysis Date:** 2026-06-05

## Languages

**Primary:**
- Python 3.10+ — entire application (`src/block_detected/`, `tests/`, `main.py`)
  - Declared in `pyproject.toml` as `requires-python = ">=3.10"`
  - README and `requirements.txt` repeat 3.10+ requirement

**Secondary:**
- HTML/CSS/JavaScript — static UI mockup only in `example_ui/stitch_block_pickup_vision_console/code.html` (not wired to runtime; reference design for future GUI work per `example_ui/stitch_block_pickup_vision_console/html_data_requirements.md`)

## Runtime

**Environment:**
- CPython (desktop local process)
- No containerization, no WSGI/ASGI server, no background worker service

**Package Manager:**
- pip (primary install path)
- Lockfile: **missing** — versions pinned only as lower bounds in `pyproject.toml` and mirrored `requirements.txt`

**Build backend:**
- setuptools ≥61 (`pyproject.toml` → `[build-system]`)
- Package layout: `src/` layout via `[tool.setuptools.packages.find] where = ["src"]`

## Frameworks

**Core (application):**
- **Ultralytics YOLO** ≥8.4.0 — object detection inference
  - Used in `src/block_detected/detection/yolo/backend.py`, `src/block_detected/detection/yolo/loader.py`
  - Loads local `.pt` weights from `models/` via `YOLO(str(model_path))`
- **OpenCV (opencv-python)** ≥4.8.0 — webcam capture, frame drawing, BGR↔RGB conversion
  - Used across `src/block_detected/io/camera/capture.py`, `src/block_detected/runtime/engine.py`, `src/block_detected/vision/drawing/`, `src/block_detected/apps/gui/app.py`
- **PySide6** ≥6.7 — desktop GUI (Qt6 bindings)
  - Primary entry: `src/block_detected/apps/gui/app.py`
  - Lazy-imported with graceful fallback when missing (`ModuleNotFoundError` guard)
  - Console script: `block-detected = block_detected.apps.gui.app:main`

**Testing:**
- **pytest** ≥8.0 — dev optional dependency (`pyproject.toml` → `[project.optional-dependencies] dev`)
  - Config: `tests/conftest.py` (adds `src/` to `sys.path`)
  - No `pytest.ini`, `pyproject.toml` `[tool.pytest]`, or coverage config detected

**Build/Dev:**
- **setuptools** — package build and editable install (`pip install -e ".[dev]"`)
- Not detected: ruff, black, mypy, pre-commit, tox, nox, uv, poetry, pip-tools

## Key Dependencies

**Direct (declared in `pyproject.toml`):**

| Package | Version constraint | Role |
|---------|-------------------|------|
| `ultralytics` | ≥8.4.0 | YOLO model load + inference |
| `opencv-python` | ≥4.8.0 | Camera I/O, image ops, legacy OpenCV window helpers |
| `PySide6` | ≥6.7 | Desktop GUI framework |
| `pytest` | ≥8.0 (dev) | Unit/smoke tests |

**Transitive (not declared; pulled by direct deps):**
- **NumPy** — array frames and test fixtures (`tests/test_widgets.py` imports `numpy`; OpenCV and Ultralytics depend on it)
- **PyTorch (`torch`)** — Ultralytics inference backend; GPU optional (README notes NVIDIA GPU as optional)
- Additional Ultralytics stack (e.g. PIL, PyYAML, matplotlib) — used internally by YOLO; not imported directly in app code

**Stdlib (significant usage):**
- `tomllib` — load TOML config (`src/block_detected/runtime/config_store.py`)
- `dataclasses`, `pathlib`, `logging`, `threading`, `collections.deque`, `typing.Protocol`

## Configuration

**Application config:**
- Typed dataclasses: `src/block_detected/runtime/config_schema.py` → `AppConfig` with sections `camera`, `inference`, `classical`, `stability`, `ui`
- Optional file: `block_detected.toml` at repo root (`src/block_detected/runtime/config_store.py` → `DEFAULT_CONFIG_PATH`)
- Defaults: `AppConfig.defaults()`; legacy constants re-exported from `src/block_detected/config/`
- Hot-reload keys: confidence, eval mode, stability filters (via `src/block_detected/runtime/config_apply.py`)
- Restart-required keys: camera index/resolution, default model name, log level (`RESTART_CAMERA_KEYS`, `RESTART_DETECTOR_KEYS` in `config_schema.py`)

**Environment variables:**
- No `.env` file present in repo (`.env` / `.env.*` gitignored)
- Application code does not read `os.environ` for config
- Test-only: `QT_QPA_PLATFORM=offscreen` in `tests/test_gui_smoke.py` for headless Qt

**Paths:**
- `src/block_detected/config/paths.py` — `PROJECT_ROOT`, `MODELS_DIR` (`models/`)

**Build:**
- `pyproject.toml` — single project manifest
- `requirements.txt` — mirrors direct deps; comment says prefer `pip install -e .`

## Platform Requirements

**Development:**
- Python 3.10+
- Webcam (for live testing)
- Editable install: `pip install -e ".[dev]"`
- Model weights: copy `.pt` files into `models/` (gitignored except `models/.gitkeep`)

**Production:**
- Desktop deployment only — local GUI process, no cloud/hosting target
- Windows, macOS, or Linux with OpenCV-compatible camera drivers
- Optional NVIDIA GPU for faster Ultralytics inference (not required by code)

**Entry points:**
- `main.py` — adds `src/` to path, calls `block_detected.apps.gui.app:main`
- `python -m block_detected` → `src/block_detected/__main__.py`
- Console script `block-detected` (after pip install)

**Run commands:**
```bash
pip install -e ".[dev]"
python main.py
python -m block_detected
block-detected
python -m pytest tests/ -q
```

## Architecture-adjacent stack notes

- Layered Python package under `src/block_detected/` (see `AGENTS.md`): `apps/` → `runtime/` → `detection/`, `vision/`, `io/`, `core/`
- `ui/input/handlers.py` retains OpenCV keyboard/mouse handlers for legacy CLI-style loop; primary UI is PySide6
- `example_ui/` — design reference only; not part of installable package or runtime stack

---

*Stack analysis: 2026-06-05*

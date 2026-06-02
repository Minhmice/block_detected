# Technology Stack

**Analysis Date:** 2026-06-02

## Languages

**Primary:**
- Python 3.10+ (`requires-python` in `pyproject.toml`) — entire application in `src/block_detected/`, `main.py`, `tests/`
- Development environment observed on Python 3.14.4 (compatible with `>=3.10`)

**Secondary:**
- Not applicable — no other application languages in repo

## Runtime

**Environment:**
- CPython (local desktop; webcam + file I/O)
- No container or server runtime configured

**Package Manager:**
- `pip` with editable install (`pip install -e ".[dev]"`)
- Lockfile: **missing** — only `requirements.txt` mirrors core deps without pinned versions

## Frameworks

**Core:**
- **Ultralytics YOLO** `>=8.4.0` — object detection inference (`detection/yolo/loader.py` imports `YOLO`)
- **OpenCV** (`opencv-python` `>=4.8.0`) — webcam capture, window display, drawing (`io/camera/capture.py`, `vision/drawing/*`, `apps/webcam/app.py`)

**Testing:**
- **pytest** `>=8.0` — dev optional dependency in `pyproject.toml`; tests in `tests/`

**Build/Dev:**
- **setuptools** `>=61` — build backend (`pyproject.toml` `[build-system]`)
- No bundler, frontend toolchain, or Docker compose in repo

## Key Dependencies

**Critical:**
- `ultralytics>=8.4.0` — loads `.pt` weights, runs `model(frame, conf=..., verbose=False)` in `apps/webcam/app.py`
- `opencv-python>=4.8.0` — `cv2.VideoCapture`, `cv2.imshow`, `cv2.waitKeyEx`, drawing primitives

**Transitive (via Ultralytics):**
- **PyTorch** — pulled by Ultralytics; CPU by default from pip; CUDA optional per user environment (documented in `README.md`)

**Infrastructure:**
- None — no database, queue, or cloud SDK in project dependencies

## Configuration

**Environment:**
- No `.env` files present in repo
- Runtime constants live in Python modules under `src/block_detected/config/`:
  - `config/paths.py` — `PROJECT_ROOT`, `MODELS_DIR`, `IMAGES_DIR`, `IMAGES_OUT_DIR`
  - `config/camera.py` — resolution, camera index
  - `config/inference.py` — confidence thresholds, default model filename
  - `config/ui.py` — window name, button layout, arrow key codes
- Barrel re-exports: `config/__init__.py`

**Build:**
- `pyproject.toml` — package metadata, dependencies, console script `block-detected-webcam`
- `requirements.txt` — minimal duplicate of runtime deps for non-editable installs

## Platform Requirements

**Development:**
- Python 3.10+
- Webcam hardware for manual webcam testing
- YOLO weights in `models/*.pt` (gitignored; copy after clone per `README.md`)
- macOS/Linux/Windows supported via OpenCV; arrow key codes in `config/ui.py` noted as platform-dependent

**Production:**
- Not applicable — desktop/local CV tool, no deployment target configured
- No CI/CD pipeline (no `.github/` workflows)

---

*Stack analysis: 2026-06-02*

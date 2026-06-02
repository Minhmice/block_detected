# Technology Stack

**Analysis Date:** 2026-06-02

## Languages

**Primary:**
- Python 3.10+ (`pyproject.toml` `requires-python`) — `src/block_detected/`, `main.py`, `tests/`

## Runtime

**Environment:**
- CPython desktop (webcam + local files)
- Optional venv at `.venv/`

**Package Manager:**
- `pip install -e ".[dev]"`
- `requirements.txt` mirrors core deps (unpinned)

## Frameworks

**Core:**
- **Ultralytics YOLO** `>=8.4.0` — `.pt` inference via `detection/yolo/backend.py`
- **OpenCV** `>=4.8.0` — camera, display, drawing (`io/camera/`, `vision/drawing/`, `apps/webcam/app.py`)

**Testing:**
- **pytest** `>=8.0` — optional dev extra

**Build:**
- **setuptools** `>=61` — `src/` layout

## Key Dependencies

**Critical:**
- `ultralytics` — `YOLO` class, `Results` API
- `opencv-python` — `VideoCapture`, `imshow`, drawing primitives
- Transitive: PyTorch (via ultralytics)

**Stdlib (no extra packages):**
- `dataclasses`, `tomllib` — typed config in `runtime/config_schema.py`, `runtime/config_store.py`
- `logging` — `runtime/logging_setup.py`

## Configuration

**Defaults:** `AppConfig.defaults()` in `runtime/config_schema.py`

**Optional file:** `block_detected.toml` at repo root (TOML load/save)

**Legacy modules:** `config/camera.py`, `config/inference.py`, `config/ui.py` — constants still used as defaults source

## Platform Requirements

**Development:**
- Webcam, display server for OpenCV window
- Model files in `models/*.pt` (gitignored)

**Production:**
- Local desktop only; no cloud services

---

*Stack analysis: 2026-06-02*

# Codebase Structure

**Analysis Date:** 2026-06-02

## Directory Layout

```
block_detected/
├── pyproject.toml
├── requirements.txt
├── main.py          # Entry: adds src/ to path, calls apps.webcam
├── AGENTS.md                   # Agent change map
├── README.md
├── tests/                      # pytest (mirrors package layers)
├── models/                     # YOLO weights (*.pt, gitignored)
├── images/                     # Sample / batch input images
└── src/block_detected/
    ├── __main__.py
    ├── apps/
    │   ├── webcam/app.py       # Webcam main loop
    │   └── batch/__init__.py   # Future batch app (stub)
    ├── config/
    │   ├── paths.py
    │   ├── camera.py
    │   ├── inference.py
    │   └── ui.py
    ├── core/types.py
    ├── detection/
    │   ├── boxes.py
    │   └── yolo/loader.py
    ├── vision/
    │   ├── geometry.py
    │   └── drawing/
    ├── io/
    │   ├── camera/capture.py
    │   └── images/__init__.py  # iter_image_paths (batch stub)
    └── ui/input/handlers.py
```

## Directory Purposes

**`src/block_detected/apps/`:**
- Purpose: Runnable application orchestration
- Contains: Webcam loop; batch stub for future
- Key files: `apps/webcam/app.py`

**`src/block_detected/config/`:**
- Purpose: Constants and paths split by domain
- Key files: `config/paths.py` (single source for PROJECT_ROOT)

**`src/block_detected/detection/`:**
- Purpose: Model loading and result parsing
- Key files: `detection/yolo/loader.py`, `detection/boxes.py`

**`src/block_detected/vision/`:**
- Purpose: Drawing and geometry without YOLO imports
- Key files: `vision/drawing/*.py`, `vision/geometry.py`

**`src/block_detected/io/`:**
- Purpose: Camera and filesystem input
- Key files: `io/camera/capture.py`, `io/images/__init__.py`

**`tests/`:**
- Purpose: Unit tests for pure modules
- Naming: `test_<module>.py` at tests root

## Key File Locations

**Entry Points:**
- `main.py`: User-facing CLI
- `src/block_detected/__main__.py`: `python -m block_detected`
- `pyproject.toml` → `block-detected-webcam` console script

**Configuration:**
- `src/block_detected/config/`: All tunables

**Core Logic:**
- Webcam loop: `src/block_detected/apps/webcam/app.py`

## Naming Conventions

**Files:** snake_case modules; `app.py` inside each app folder

**Packages:** Do not create `block_detected/models/` (conflicts with repo `models/`)

**Imports:** Import submodules directly; package `__init__.py` files stay lightweight (no OpenCV at import time)

## Where to Add New Code

| Feature | Location |
|---------|----------|
| New realtime app | `apps/<name>/app.py` |
| Batch inference | `apps/batch/app.py` + use `io/images/` |
| New detector backend | `detection/onnx/` |
| Tracking | `vision/tracking/` |
| Tests | `tests/test_<area>.py` |

## Special Directories

**`models/`:**
- Committed: `.gitkeep` only; `*.pt` gitignored

**`.planning/`:**
- GSD planning artifacts; `codebase/` is reference docs

---

*Structure analysis: 2026-06-02*

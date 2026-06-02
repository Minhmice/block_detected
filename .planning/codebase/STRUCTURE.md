# Codebase Structure

**Analysis Date:** 2026-06-02

## Directory Layout

```
block_detected/                    # repo root (PROJECT_ROOT)
├── pyproject.toml               # package metadata, deps, console script
├── requirements.txt             # runtime deps mirror (unpinned)
├── main.py                      # webcam CLI entry (sys.path bootstrap)
├── AGENTS.md                    # agent change map + layer rules
├── README.md                    # user install/run docs (VI + EN mix)
├── models/                      # YOLO weights (*.pt gitignored)
├── images/                      # batch input folder (usage in Phase 3)
├── images_out/                  # batch output (gitignored)
├── src/block_detected/          # installable package
│   ├── __init__.py
│   ├── __main__.py
│   ├── apps/
│   │   ├── webcam/app.py
│   │   └── batch/__init__.py    # stub
│   ├── config/
│   ├── core/
│   ├── detection/
│   ├── vision/
│   ├── io/
│   └── ui/
├── tests/                       # pytest
│   ├── conftest.py
│   └── test_*.py
└── .planning/                   # GSD roadmap, phases, codebase map
    └── codebase/                # this documentation set
```

## Directory Purposes

**`src/block_detected/apps/`:**
- Purpose: Runnable application orchestration
- Contains: `webcam/app.py` (implemented), `batch/__init__.py` (stub)
- Key files: `apps/webcam/app.py`

**`src/block_detected/config/`:**
- Purpose: Domain-split constants (no business logic)
- Contains: `paths.py`, `camera.py`, `inference.py`, `ui.py`, `__init__.py` re-exports
- Key files: `config/paths.py` for all filesystem roots

**`src/block_detected/core/`:**
- Purpose: Shared types without OpenCV/YOLO
- Contains: `types.py` (`Box`)
- Key files: `core/types.py`

**`src/block_detected/detection/`:**
- Purpose: Model loading and result parsing
- Contains: `boxes.py`, `yolo/loader.py`
- Key files: `detection/yolo/loader.py`

**`src/block_detected/vision/`:**
- Purpose: Geometry and frame annotation
- Contains: `geometry.py`, `drawing/overlays.py`, `eval.py`, `widgets.py`
- Key files: `vision/drawing/widgets.py`

**`src/block_detected/io/`:**
- Purpose: Camera and filesystem inputs
- Contains: `camera/capture.py`, `images/__init__.py`
- Key files: `io/images/__init__.py` → `iter_image_paths`

**`src/block_detected/ui/`:**
- Purpose: OpenCV keyboard/mouse handlers
- Contains: `input/handlers.py`
- Key files: `ui/input/handlers.py`

**`tests/`:**
- Purpose: Unit tests for pure/config/io modules
- Contains: `conftest.py`, `test_geometry.py`, `test_boxes.py`, `test_config_paths.py`, `test_io_images.py`
- Key files: `tests/conftest.py` (adds `src/` to path)

**`models/`:**
- Purpose: Local YOLO weight files
- Generated: user-provided
- Committed: `.gitkeep` only; `*.pt` gitignored

## Key File Locations

**Entry Points:**
- `main.py`: Run webcam without editable install (path bootstrap)
- `src/block_detected/__main__.py`: `python -m block_detected`
- `src/block_detected/apps/webcam/app.py`: `main()` implementation

**Configuration:**
- `pyproject.toml`: Package name, dependencies, `block-detected-webcam` script
- `src/block_detected/config/paths.py`: `PROJECT_ROOT`, asset directories
- `src/block_detected/config/inference.py`: `DEFAULT_MODEL_NAME`, confidence constants
- `src/block_detected/config/camera.py`: Resolution and camera index
- `src/block_detected/config/ui.py`: Window name, key codes

**Core Logic:**
- `src/block_detected/apps/webcam/app.py`: Webcam main loop
- `src/block_detected/detection/boxes.py`: YOLO → `list[Box]`
- `src/block_detected/detection/yolo/loader.py`: Model discovery/load

**Testing:**
- `tests/conftest.py`: Ensures `src/` on `sys.path`
- `tests/test_*.py`: Module-specific unit tests

## Naming Conventions

**Files:**
- Snake_case modules: `app.py`, `handlers.py`, `loader.py`
- Test modules: `test_<module>.py` mirroring package area (`test_geometry.py`, `test_io_images.py`)

**Directories:**
- Lowercase layer names: `apps`, `config`, `detection`, `vision`, `io`, `ui`
- Subpackages by concern: `yolo/`, `drawing/`, `camera/`, `input/`

**Functions:**
- snake_case verbs: `open_camera`, `extract_boxes`, `iter_image_paths`, `draw_status_bar`

**Types:**
- `Box` as `TypeAlias` for coordinate tuple in `core/types.py`

## Where to Add New Code

**New webcam behavior (keys, UI):**
- Key handling: `src/block_detected/ui/input/handlers.py`
- New constants: `src/block_detected/config/ui.py` or `inference.py`
- Drawing: `src/block_detected/vision/drawing/` (not in `apps/webcam/app.py`)

**Batch image inference (Phase 3):**
- App loop: create `src/block_detected/apps/batch/app.py`
- Image listing: extend `src/block_detected/io/images/__init__.py` if needed
- Square-box drawing: `src/block_detected/vision/drawing/annotators/square.py` (planned)
- Console script: add `block-detected-batch` in `pyproject.toml` `[project.scripts]`
- Tests: `tests/test_square.py` or similar

**New detector backend (e.g. ONNX):**
- Create `src/block_detected/detection/onnx/` parallel to `yolo/`
- Keep parsing in `detection/boxes.py` or shared parser module

**New config values:**
- Always add to appropriate `config/*.py`; re-export from `config/__init__.py` if used widely
- Never hardcode repo paths outside `config/paths.py`

**Unit tests:**
- `tests/test_<feature>.py` next to existing tests
- Use fakes for Ultralytics tensors (pattern in `tests/test_boxes.py`)

## Special Directories

**`.planning/`:**
- Purpose: GSD roadmap, phase plans, verification artifacts
- Generated: planning workflow output
- Committed: yes (except transient local state)

**`.planning/codebase/`:**
- Purpose: Codebase map for planners/executors (`STACK.md`, `ARCHITECTURE.md`, etc.)
- Generated: `/gsd-map-codebase`
- Committed: yes

**`.venv/`:**
- Purpose: Local virtual environment
- Generated: yes
- Committed: no (gitignored)

**`images_out/`, `runs/`, `wandb/`:**
- Purpose: Inference/training output
- Generated: yes at runtime
- Committed: no

---

*Structure analysis: 2026-06-02*

# Architecture

**Analysis Date:** 2026-06-02

## Pattern Overview

**Overall:** Layered package architecture for computer vision — thin application loops orchestrating config, I/O, detection, vision rendering, and UI input.

**Key Characteristics:**
- Strict dependency direction: `apps` → `detection` / `vision` / `io` / `ui` / `config`; `core` has no OpenCV/YOLO imports
- `detection` must not import `apps` or `ui` (documented in `AGENTS.md`)
- `vision` must not import `detection` — drawing uses frames/boxes passed in or Ultralytics `result.plot()` at app boundary
- Configuration is constants-only modules, not runtime env injection

## Layers

**Apps (orchestration):**
- Purpose: Main loops and CLI entry orchestration
- Location: `src/block_detected/apps/`
- Contains: `webcam/app.py` (live inference loop); `batch/__init__.py` (stub for Phase 3)
- Depends on: `config`, `core`, `detection`, `io`, `ui`, `vision`
- Used by: `main.py`, `__main__.py`, console script `block-detected-webcam`

**Config (constants):**
- Purpose: Centralize paths, camera, inference thresholds, UI constants
- Location: `src/block_detected/config/`
- Contains: `paths.py`, `camera.py`, `inference.py`, `ui.py`, barrel `__init__.py`
- Depends on: stdlib only (`pathlib` in `paths.py`)
- Used by: all other layers

**Core (domain types):**
- Purpose: Shared types without CV framework imports
- Location: `src/block_detected/core/types.py`
- Contains: `Box` type alias `tuple[int,int,int,int]`
- Depends on: `typing` only
- Used by: `detection/boxes.py`, `vision/drawing/overlays.py`, `apps/webcam/app.py`

**Detection (models + parsing):**
- Purpose: Load YOLO weights and parse inference outputs to `Box` lists
- Location: `src/block_detected/detection/`
- Contains: `boxes.py` (`extract_boxes`), `yolo/loader.py` (`discover_model_paths`, `load_yolo`)
- Depends on: `ultralytics`, `config`, `core`
- Used by: `apps/webcam/app.py` (future: `apps/batch/app.py`)

**Vision (geometry + drawing):**
- Purpose: Pure geometry and OpenCV drawing helpers — no model imports
- Location: `src/block_detected/vision/`
- Contains: `geometry.py`, `drawing/overlays.py`, `drawing/eval.py`, `drawing/widgets.py`
- Depends on: `cv2`, `core`, `config` (widgets)
- Used by: `apps/webcam/app.py`, `ui/input/handlers.py` (geometry hit-test)

**IO (devices + files):**
- Purpose: Webcam capture and image path enumeration
- Location: `src/block_detected/io/`
- Contains: `camera/capture.py`, `images/__init__.py` (`iter_image_paths`)
- Depends on: `cv2` (camera), `config` (camera sizes)
- Used by: `apps/webcam/app.py`; batch app will use `io/images`

**UI (input):**
- Purpose: Keyboard and mouse handling for OpenCV window
- Location: `src/block_detected/ui/input/handlers.py`
- Depends on: `cv2`, `config`, `vision.geometry`
- Used by: `apps/webcam/app.py`

## Data Flow

**Webcam inference loop (`apps/webcam/app.py`):**

1. `discover_model_paths()` → sorted `models/*.pt`; `load_yolo()` loads Ultralytics model
2. `open_camera(CAMERA_INDEX)` sets resolution from `config/camera.py`
3. Each frame: `cap.read()` → `model(frame, conf=..., verbose=False)` → `extract_boxes(result)` for overlay history
4. Annotate: eval mode uses `draw_eval_boxes` on copy; normal mode uses `result.plot()` + optional `draw_overlay_history`
5. `draw_status_bar`, `draw_model_switch_button` → `cv2.imshow` + `waitKeyEx` → `handle_key` / camera switch / quit
6. `finally`: release capture, destroy windows

**State Management:**
- Loop-local variables in `main()`: `conf`, `overlay_enabled`, `eval_mode`, `box_history` (`deque` of `list[Box]`), `ui_state` dict for mouse callback (`button_rect`, `switch_model`)
- No global mutable application state or persistence layer

## Key Abstractions

**Box:**
- Purpose: Integer axis-aligned detection rectangle `(x1, y1, x2, y2)`
- Examples: `src/block_detected/core/types.py`
- Pattern: `TypeAlias` for tuple; produced by `detection/boxes.extract_boxes`

**YOLO loader:**
- Purpose: Discover and load `.pt` files from `MODELS_DIR`
- Examples: `src/block_detected/detection/yolo/loader.py`
- Pattern: Functions returning `list[Path]` and `YOLO` instance; default model name from `config/inference.py`

**Fake result test doubles:**
- Purpose: Unit-test `extract_boxes` without Ultralytics
- Examples: `tests/test_boxes.py` (`_FakeResult`, `_FakeBoxes`)

## Entry Points

**`main.py` (repo root):**
- Triggers: `python main.py`
- Responsibilities: Insert `src/` on `sys.path` if needed; delegate to `block_detected.apps.webcam.app.main`

**`python -m block_detected`:**
- Location: `src/block_detected/__main__.py`
- Triggers: module execution
- Responsibilities: Same as webcam `main()`

**Console script:**
- Location: `pyproject.toml` → `block-detected-webcam = block_detected.apps.webcam.app:main`
- Triggers: `block-detected-webcam` after `pip install -e .`

## Error Handling

**Strategy:** Print tagged messages and return exit codes from `main()`; break or return on unrecoverable errors in loop.

**Patterns:**
- Missing models: `[ERROR] No .pt models found` → return `1` (`apps/webcam/app.py`)
- Model load failure: try/except around `load_yolo`, return `1`
- Per-frame inference failure: `[ERROR] Inference failed` → break loop
- Camera read failure: `[WARN] Camera frame read failed` → break loop
- `finally` block always releases camera and destroys OpenCV windows

## Cross-Cutting Concerns

**Logging:** `print("[INFO|WARN|ERROR] ...")` — no structured logging module

**Validation:** Minimal — directory existence checks in `discover_model_paths`, `iter_image_paths`; confidence clamped in `handle_key` via `CONF_MIN`/`CONF_MAX`

**Authentication:** Not applicable

---

*Architecture analysis: 2026-06-02*

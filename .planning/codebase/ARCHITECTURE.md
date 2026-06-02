# Architecture

**Analysis Date:** 2026-06-02

## Pattern Overview

**Overall:** Layered CV package (apps → detection/vision/io/ui → config/core)

**Key Characteristics:**
- Thin application loops in `apps/`
- YOLO isolated under `detection/yolo/`
- OpenCV drawing isolated under `vision/`
- Config split by domain under `config/`

## Layers

**Apps:**
- Purpose: Orchestrate frame loop, wire layers
- Location: `src/block_detected/apps/`
- Depends on: detection, vision, io, ui, config
- Used by: `run_yolo_webcam.py`, console script

**Detection:**
- Purpose: Load models, run inference, parse boxes
- Location: `src/block_detected/detection/`
- Depends on: config, core, ultralytics
- Must not import: apps, ui

**Vision:**
- Purpose: Annotate frames, geometry helpers
- Location: `src/block_detected/vision/`
- Depends on: core, opencv (in drawing modules only)
- Must not import: detection

**IO:**
- Purpose: Webcam capture; image path enumeration
- Location: `src/block_detected/io/`
- Depends on: config, opencv (camera module)

**UI:**
- Purpose: Keyboard and mouse handlers
- Location: `src/block_detected/ui/`
- Depends on: config, vision.geometry

**Config / Core:**
- Purpose: Paths, thresholds, shared `Box` type
- Location: `config/`, `core/`

## Data Flow

**Webcam realtime:**

1. `apps/webcam/app.py` opens camera via `io/camera/capture.py`
2. Each frame: `YOLO(frame)` via model loaded from `detection/yolo/loader.py`
3. Boxes parsed in `detection/boxes.py`
4. Frame annotated via `vision/drawing/` (or `result.plot()` in normal mode)
5. Input handled by `ui/input/handlers.py`
6. Display via OpenCV in app loop

## Key Abstractions

**Box:**
- Type: `tuple[int,int,int,int]` in `core/types.py`
- Used across detection output and vision overlays

**Model loader:**
- `discover_model_paths`, `load_yolo` in `detection/yolo/loader.py`

## Entry Points

**Webcam:**
- Location: `src/block_detected/apps/webcam/app.py` → `main()`
- Triggers: `python run_yolo_webcam.py`, `block-detected-webcam`

## Error Handling

**Strategy:** Print `[ERROR]` / `[WARN]` and return exit code from `main()`

**Patterns:**
- Missing models: exit 1 before loop
- Camera failure: exit 1 at startup
- Inference errors: break loop, cleanup in `finally`

## Cross-Cutting Concerns

**Logging:** stdout prints with level prefix

**Configuration:** `config/` modules only

**Testing:** pytest on pure modules (`geometry`, `boxes`, `paths`, `io/images`) without loading OpenCV via package `__init__.py`

---

*Architecture analysis: 2026-06-02*

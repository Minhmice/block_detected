# Architecture

**Analysis Date:** 2026-06-30

## Pattern Overview

**Overall:** One Python package (`src/block_detected/`) providing a **shared detection runtime** (camera → preprocess → YOLO → postprocess → render → metrics) with **three thin app shells**:

- **View**: OpenCV window preview (`src/view/`)
- **TUI**: Textual dashboard (`src/block_detected/tui/`)
- **Stream**: Raspberry Pi JPEG server + LAN viewer (`src/stream/`) — intentionally standalone

Evidence:

- Launcher routes: `main.py` (selects `stream` / `view` / `tui`)
- View entry: `src/view/app.py` imports `block_detected.runtime.engine.WebcamEngine`
- TUI entry: `src/block_detected/tui/app.py` imports `block_detected.runtime.engine.WebcamEngine`
- Stream is separate: `src/stream/__main__.py` only imports within `stream.*` (no `block_detected` import)
- Dependency intent documented: `AGENTS.md`

## Runtime Pipeline (Shared)

### Core orchestrator

- **Facade**: `src/block_detected/runtime/engine.py` → `WebcamEngine`
  - Loads available model weights from `block_detected.config.paths.MODELS_DIR` and `block_detected.detection.yolo.loader.discover_model_paths()`
  - Owns session state (`src/block_detected/runtime/state.py`), metrics (`src/block_detected/runtime/metrics.py`), and stability postprocess (`src/block_detected/runtime/postprocess.py`)

### Single-frame data flow

The heart of the pipeline is **one frame** processed by:

- `src/block_detected/runtime/frame_loop.py` → `process_single_frame(...)`
  - **Read**: `cap.read()` on either `cv2.VideoCapture` or Pi camera adapters (`src/block_detected/io/camera/capture.py`)
  - **Preprocess**: `src/block_detected/runtime/preprocess.py` → `apply_preprocess(...)` (contrast/brightness/saturation + optional blur)
  - **Infer**: `DetectorBackend.predict(...)` (protocol in `src/block_detected/core/protocols.py`)
    - Current implementation: `src/block_detected/detection/yolo/backend.py`
  - **Postprocess**: `src/block_detected/runtime/postprocess.py` (`DetectionPostProcessor.process(...)`)
  - **Render**: `src/block_detected/runtime/render.py` → `render_frame(...)`
    - Adds UI overlay elements via `src/block_detected/vision/drawing/widgets.py` (e.g., model switch button)
  - **Metrics**: `src/block_detected/runtime/metrics.py` (`RuntimeMetrics.record(...)`)
  - **Status**: returns `RuntimeStatus` (`src/block_detected/core/domain.py`) + annotated frame + top detections

### Camera session management

- Open/switch camera lives in `src/block_detected/runtime/session.py`
  - `try_open_camera(...)` supports **desktop camera index** and **Pi camera source selection**
  - Pi detection and branching is in `src/block_detected/runtime/platform.py` (`is_raspberry_pi()`)

## Configuration Architecture

### Typed config

- Config schema: `src/block_detected/config/schema.py` (`AppConfig` + nested dataclasses)
  - Restart boundaries expressed as key sets:
    - `RESTART_CAMERA_KEYS` (e.g. `camera.*` including `camera.source`)
    - `RESTART_DETECTOR_KEYS` (e.g. `inference.imgsz`)

### Storage and migration

- Config load/save: `src/block_detected/config/store.py`
  - Default path: `DEFAULT_CONFIG_PATH = PACKAGE_ROOT / "block_detected.json"`
  - Legacy migration (on first load):
    - `block_detected.toml` at repo root (`LEGACY_TOML_PATH`)
    - `block_detected.json` at repo root (`LEGACY_ROOT_JSON`)

Evidence: `src/block_detected/config/store.py` functions `load_config()`, `save_config()`, `_migrate_legacy_config_if_needed()`.

## Application Shells

### Launcher / bootstrap

- **Launcher**: `main.py`
  - Picks mode by argv flags (`--stream`, `--view`, `--tui`), explicit subcommand (`stream|view|tui`), or env var (`BLOCK_DETECTED_UI`)
  - Dispatches into:
    - `stream.__main__.main`
    - `view.app.main`
    - `block_detected.tui.app.main`
- **Bootstrap**: `bootstrap.py`
  - Detects device (`detect_device()`)
  - Auto-installs deps into the environment (desktop: `pip install -e ".[view]"`; Pi: `requirements-pi.txt` + `pip install -e . --no-deps`)

### View (OpenCV window)

- Entry: `src/view/app.py`
  - Validates config (`block_detected.config.store.validate_config`)
  - Runs `WebcamEngine.process_frame()` loop with:
    - keyboard/mouse input: `src/view/input.py`
    - config reload: `src/view/reload.py` (triggered by `r`)

### TUI (Textual dashboard)

- Entry: `src/block_detected/tui/app.py`
  - Wraps `WebcamEngine` in a small controller (`TuiRuntime`) for start/stop and hot updates
  - Applies runtime hot settings via `src/block_detected/runtime/config_apply.py` (`apply_hot_runtime_settings`)

### Stream (Pi server + viewer)

- Entry: `src/stream/__main__.py`
  - Server: `src/stream/server.py` (TCP stream + UDP discovery)
  - Viewer: `src/stream/viewer.py` (Tkinter UI + OpenCV window; LAN discovery + manual IP fallback)

This stack is **intentionally separate** from the detection runtime (see `AGENTS.md` dependency rule: “stream → standalone”).

## Dependency Direction (Enforced by Convention)

Documented in `AGENTS.md`:

- **View** (`src/view/`) → depends on `block_detected.runtime`
- **TUI** (`src/block_detected/tui/`) → depends on `block_detected.runtime`
- **Stream** (`src/stream/`) → standalone (no `block_detected` imports)

Within `block_detected/`:

- **Config** (`src/block_detected/config/`) is foundational (schema + storage + constants)
- **Core types/protocols** (`src/block_detected/core/`) define shared domain objects and the detector contract
- **Detection backend** (`src/block_detected/detection/`) implements Ultralytics YOLO adapter
- **IO + Vision** (`src/block_detected/io/`, `src/block_detected/vision/`) support the runtime
- **Runtime** (`src/block_detected/runtime/`) orchestrates everything for apps to call

## Packaging & Entry Points

Defined in `pyproject.toml`:

- Console scripts:
  - `block-detected = "main:main"`
  - `block-detected-stream = "stream.__main__:main"`
  - `block-detected-view = "view.app:main"`
  - `block-detected-tui = "block_detected.tui.app:main"`
- Optional extras for feature sets:
  - `view` includes `opencv-python` (needed for `cv2.imshow`, see `main.py` check)
  - `tui` includes `textual` + `rich`


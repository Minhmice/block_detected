# Architecture

**Analysis Date:** 2025-06-05

## Pattern Overview

**Overall:** Layered monolith with a dedicated runtime orchestration layer and thin application shell.

**Key Characteristics:**
- Strict dependency direction: `core` → `detection`/`vision`/`io` → `runtime` → `apps`
- Domain types and protocols live in `core` with zero OpenCV/YOLO imports
- `WebcamEngine` in `runtime/engine.py` owns the frame loop (read → infer → postprocess → render → metrics)
- PySide6 GUI runs the engine on a `QThread`; UI never duplicates camera or inference logic
- Typed `AppConfig` dataclasses with TOML persistence and hot-reload vs restart key classification

## Layers

**Application (`apps/`):**
- Purpose: User-facing entry points and orchestration only
- Location: `src/block_detected/apps/`
- Contains: PySide6 desktop GUI (`apps/gui/app.py`)
- Depends on: `runtime` (engine, config, logging)
- Used by: `main.py`, `block_detected.__main__`, console script `block-detected`

**Runtime (`runtime/`):**
- Purpose: Engine loop, session state, metrics, config schema/store, post-processing orchestration, detector loading
- Location: `src/block_detected/runtime/`
- Contains: `WebcamEngine`, `RuntimeState`, `RuntimeMetrics`, `DetectionPostProcessor`, `AppConfig`, TOML load/save, logging ring buffer
- Depends on: `core`, `detection`, `vision`, `io`, `config`
- Used by: `apps/gui/app.py`, tests

**Core (`core/`):**
- Purpose: Domain model and backend protocol — no third-party CV/ML imports
- Location: `src/block_detected/core/`
- Contains: `Box`, `Detection`, `FrameResult`, `InferenceStats`, `RuntimeStatus`, `DetectorBackend` Protocol
- Depends on: stdlib only
- Used by: `detection`, `runtime`, `vision`, `postprocess`

**Detection (`detection/`):**
- Purpose: YOLO backend and raw-result parsing into domain types
- Location: `src/block_detected/detection/`
- Contains: `parse_yolo_result` in `boxes.py`, `YoloDetector` in `yolo/backend.py`, model discovery in `yolo/loader.py`
- Depends on: `core`, `config` (paths/inference constants), Ultralytics
- Used by: `runtime/detector_loader.py`, `runtime/engine.py`

**Vision (`vision/`):**
- Purpose: Pure geometry and OpenCV drawing — no detection module imports
- Location: `src/block_detected/vision/`
- Contains: `geometry.py` (IoU, box area), `drawing/detections.py`, `drawing/eval.py`, `drawing/widgets.py`
- Depends on: `core`, `config` (UI constants), OpenCV
- Used by: `runtime/engine.py`, `runtime/postprocess.py`, `ui/input/handlers.py`

**IO (`io/`):**
- Purpose: Hardware and stream access
- Location: `src/block_detected/io/camera/`
- Contains: `open_camera`, `switch_camera` in `capture.py`
- Depends on: OpenCV only
- Used by: `runtime/engine.py`

**UI input (`ui/`):**
- Purpose: OpenCV-window keyboard/mouse handlers (legacy/debug path; GUI uses Qt widgets instead)
- Location: `src/block_detected/ui/input/handlers.py`
- Contains: `handle_key`, `on_mouse`
- Depends on: `runtime` config/state, `vision/geometry`
- Used by: Re-exported from `ui/__init__.py`; not wired into current PySide6 GUI loop

**Config (`config/`):**
- Purpose: Legacy path constants and module-level defaults that `AppConfig` mirrors
- Location: `src/block_detected/config/`
- Contains: `paths.py` (`PROJECT_ROOT`, `MODELS_DIR`), `camera.py`, `inference.py`, `ui.py`
- Depends on: stdlib
- Used by: `runtime/config_schema.py`, `detection/yolo/loader.py`, `vision/drawing/widgets.py`

## Dependency Rules

Enforced by design (documented in `AGENTS.md`):

| Layer | Must NOT import |
|-------|-----------------|
| `core` | OpenCV, Ultralytics, PySide6 |
| `detection` | `apps`, `ui`, `runtime` |
| `vision` | `detection` |
| `runtime` | `apps`, `ui` |
| `apps` | Direct YOLO/camera logic (delegate to `WebcamEngine`) |

**Detector indirection:** `runtime/detector_loader.py` returns `DetectorBackend`; only implementation is `YoloDetector`. Swap backends by changing the loader, not the engine.

## Data Flow

**Frame processing loop (`WebcamEngine.process_frame`):**

1. **Read** — `io/camera/capture.py` → `VideoCapture.read()` → BGR frame
2. **Infer** — `DetectorBackend.predict(frame, conf=...)` → `FrameResult` with `list[Detection]` + raw YOLO result
3. **Postprocess** — `DetectionPostProcessor.process()` applies spatial filters, duplicate merge, temporal stability when `stability.enabled`
4. **Render** — `_render()` chooses eval vs normal vs stability drawing path; overlays status bar and model-switch button
5. **Metrics** — `RuntimeMetrics.record()` computes FPS and per-stage ms latencies → `InferenceStats`
6. **Return** — `ProcessedFrame(annotated, button_rect, status)` to caller

**GUI thread model:**

1. `MainWindow` starts `FrameThread` (`QThread`) with run-generation guard
2. Worker creates `WebcamEngine.try_create()` → `try_start()` → loop `process_frame()` until stop or read failure
3. `frame_ready` signal emits `QImage` + `RuntimeStatus` to main thread for preview and status labels
4. User controls queue pending changes (confidence, eval mode, hot config, model/camera switch) via thread-safe locks; applied at start of each loop iteration via `apply_hot_runtime_settings()`
5. Logs polled every 500 ms via `get_log_lines()` (never read `LogBufferHandler._records` from UI)
6. Shutdown: `engine.shutdown(destroy_cv_windows=False)` in worker; main thread waits for `finished` before clearing `frame_thread`

**Config flow:**

1. Startup: `load_config()` reads optional `block_detected.toml` at repo root → `AppConfig.from_dict()` or defaults
2. Validation: `AppConfig.validate()` before GUI launch
3. Hot reload: confidence, eval mode, all `stability.*` fields via `engine.apply_hot_config()` without restart
4. Restart required: `camera.*`, `inference.default_model_name`, `ui.log_level` — detected by `needs_runtime_restart()` in `runtime/config_apply.py`

**State Management:**
- **Persistent config:** `AppConfig` dataclass, saved to TOML via `runtime/config_store.py`
- **Session state:** `RuntimeState` (confidence, eval_mode, camera_index, model_index) — mutable per run, hot-updated from GUI
- **Postprocess state:** `TemporalStabilityTracker` sliding window inside `DetectionPostProcessor`; reset on model switch
- **Metrics state:** Rolling 30-frame deque for FPS averaging in `RuntimeMetrics`

## Key Abstractions

**DetectorBackend Protocol:**
- Purpose: Pluggable object detector interface
- Location: `src/block_detected/core/protocols.py`
- Pattern: `@runtime_checkable` Protocol with `model_name`, `predict()`, `close()`
- Implementation: `detection/yolo/backend.py` → `YoloDetector`

**FrameResult / Detection:**
- Purpose: Normalized inference output independent of Ultralytics
- Location: `src/block_detected/core/domain.py`, parsing in `detection/boxes.py`
- Pattern: `Detection` holds `Box`, class metadata, confidence; `FrameResult` bundles detections + optional raw backend object for eval rendering

**WebcamEngine:**
- Purpose: Single orchestrator for webcam block-detection session
- Location: `src/block_detected/runtime/engine.py`
- Pattern: Factory methods `try_create()` / `create()`; lifecycle `try_start()` → `process_frame()` → `shutdown()`

**AppConfig:**
- Purpose: Typed, validated, TOML-serializable application settings
- Location: `src/block_detected/runtime/config_schema.py`
- Pattern: Nested dataclasses (`CameraConfig`, `InferenceConfig`, `StabilityConfig`, etc.); `RESTART_CAMERA_KEYS` / `RESTART_DETECTOR_KEYS` frozensets

**DetectionPostProcessor:**
- Purpose: Config-driven spatial and temporal filtering pipeline
- Location: `src/block_detected/runtime/postprocess.py`
- Pattern: Pure filter functions + stateful `TemporalStabilityTracker`; enabled only when `stability.enabled`

## Entry Points

**Primary GUI:**
- Location: `main.py` → `block_detected.apps.gui.app.main`
- Triggers: `python main.py`, `python -m block_detected`, `block-detected` console script
- Responsibilities: Load/validate config, setup logging, launch `QApplication` + `MainWindow`

**Package module:**
- Location: `src/block_detected/__main__.py`
- Triggers: `python -m block_detected`
- Responsibilities: Same as GUI main

**Dev path bootstrap:**
- Location: `main.py` inserts `src/` into `sys.path` before import (editable install also works via `pip install -e .`)

## Error Handling

**Strategy:** Log and degrade gracefully; return optional/error tuples rather than raising in hot paths.

**Patterns:**
- `WebcamEngine.try_create()` → `(engine | None, error_message | None)` when models missing or load fails
- `WebcamEngine.try_start()` → `(bool, error_message | None)` when camera open fails
- `process_frame()` returns `None` on read failure or inference exception; worker thread emits `error` signal and exits loop
- Model/camera switch catches load failures, logs error, keeps previous detector/camera
- Config validation collects all errors in a list before GUI launch; invalid config exits with code 1

## Cross-Cutting Concerns

**Logging:** `runtime/logging_setup.py` — root logger with stdout + `LogBufferHandler` ring buffer (500 lines); GUI reads via `get_log_lines()`. Ultralytics logger capped at WARNING.

**Validation:** `AppConfig.validate()` in `config_schema.py` — type checks, range checks, stability vote/window consistency. `validate_config()` wrapper in `config_store.py`.

**Authentication:** Not applicable — local desktop app, no network auth.

**Thread safety:** GUI worker uses `threading.Event` for stop, `threading.Lock` for pending control queue; log buffer uses lock in `snapshot_lines()`.

---

*Architecture analysis: 2025-06-05*

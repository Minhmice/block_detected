# Architecture

**Analysis Date:** 2026-06-02

## Pattern Overview

**Overall:** Layered CV package with **runtime engine** between thin app and detection/vision/io.

**Detection:** Ultralytics YOLO only (`.pt` weights). No alternate inference runtime in repo.

## Layers

**Apps (`apps/webcam/app.py`):**
- Load config, validate, setup logging
- Create `WebcamEngine`, OpenCV window, delegate input
- Does not call YOLO or parse boxes directly

**Runtime (`runtime/`):**
- `engine.py` — `WebcamEngine`: read frame → `load_detector` → predict → render → metrics
- `state.py` — confidence, overlay, eval mode, box history
- `metrics.py` — FPS, read/infer/render ms
- `config_schema.py` / `config_store.py` — typed `AppConfig`, TOML
- `detector_loader.py` — `load_detector(path)` → `YoloDetector`
- `logging_setup.py` — stdout + ring buffer

**Detection (`detection/`):**
- `yolo/loader.py` — discover `.pt` files
- `yolo/backend.py` — `YoloDetector` implements `DetectorBackend`
- `boxes.py` — `parse_yolo_result()` → `FrameResult` / `Detection`

**Vision (`vision/`):**
- Drawing and geometry only; no YOLO imports
- `drawing/widgets.py` — status bar (optional FPS line), model button

**IO (`io/camera/`):**
- `open_camera(index, width, height)`, `switch_camera(...)`

**UI (`ui/input/`):**
- `handle_key`, `on_mouse` — updates `RuntimeState`, logging

**Core (`core/`):**
- `domain.py` — `Detection`, `FrameResult`, `InferenceStats`, `RuntimeStatus`
- `protocols.py` — `DetectorBackend` (implemented by YOLO only)
- `types.py` — `Box`

## Data Flow (webcam)

1. `main.py` → `apps.webcam.app.main()`
2. `load_config()` → `WebcamEngine.create(config)`
3. Loop: `engine.process_frame()`
   - `cap.read()` timed
   - `detector.predict(frame, conf=...)`
   - Normal mode: `raw.plot()` + optional overlay history
   - Eval mode: `frame.copy()` + `draw_eval_boxes`
   - Status bar + model button
4. Input: `handle_key` / `switch_camera` / `switch_model`
5. `engine.shutdown()` releases camera

## Key Abstractions

**DetectorBackend:** Protocol in `core/protocols.py`; single implementation `YoloDetector`.

**AppConfig:** Dataclass groups — camera, inference, classical (stub), stability (stub), ui.

**Hot reload vs restart:**
- Hot: confidence, overlay, eval (runtime state)
- Restart camera: index, width, height
- Restart detector: default model name change (reload `.pt`)

## Entry Points

- `main.py` — primary CLI
- `python -m block_detected` → `__main__.py`
- `block-detected-webcam` console script → `apps.webcam.app:main`

## Error Handling

- Config validation → log errors, exit 1
- Missing models / camera → log error, exit before loop
- Inference failure → log and break loop
- `finally`: `engine.shutdown()`

---

*Architecture analysis: 2026-06-02*

# Roadmap: Detect Only v4 (Milestone v2.0)

**Milestone:** v2.0 Detect Only v4  
**Created:** 2026-07-03  
**Phase numbering:** Continues from v1.0 (phases 1–2 complete) → starts at Phase 3  
**Module:** `src/detect_only_v4/` (greenfield)

---

## Overview

| Phase | Name | Goal | Requirements | Success Criteria |
|-------|------|------|--------------|------------------|
| 3 | Core API & Contracts | Types, inspect_model, public API surface | CORE-01–06 | 5 |
| 4 | Model Discovery & Formats | Scan models/, multi-format load | MODEL-01–05 | 5 |
| 5 | Task Adapters & Overlay | 4 task adapters + draw_overlay | ADPT-01–08 | 6 |
| 6 | Camera Discovery & Backends | V4L2, Picamera2, probe_camera | CAM-01–06 | 5 |
| 7 | Threaded Pipeline | Bounded queue, capture/infer threads | PIPE-01–06 | 5 |
| 8 | FastAPI WebSocket UI | REST + live stream + runtime config | WEB-01–08 | 6 |
| 9 | Pi Optimization & Hardening | NCNN priority, tests, README, packaging | QA-01–05 | 5 |

**Total:** 7 phases | 42 requirements | 100% mapped ✓

---

## Phase 3: Core API & Contracts

**Goal:** Establish `DetectionResult`, protocols, logging, and `inspect_model` with authoritative task/family resolution — foundation for all downstream phases.

**Requirements:** CORE-01, CORE-02, CORE-03, CORE-04, CORE-05, CORE-06

**Plans:** 2 plans

Plans:
**Wave 1**

- [ ] 03-01-PLAN.md — Core types, protocols, errors, logging, greenfield gate

**Wave 2** *(blocked on Wave 1 completion)*

- [ ] 03-02-PLAN.md — inspect_model chain, public API stubs/exports, full test suite

**Deliverables:**

- `src/detect_only_v4/core/types.py` — DetectionResult, ModelInfo, CameraInfo, InferConfig
- `src/detect_only_v4/core/protocols.py` — CameraBackend, ModelBackend, TaskAdapter ABCs
- `src/detect_only_v4/core/errors.py` — typed exceptions
- `src/detect_only_v4/models/inspector.py` — inspect_model()
- `src/detect_only_v4/__init__.py` — public API re-exports
- Package skeleton with logging setup

**Success criteria:**

1. `DetectionResult` serializes to JSON with all fields; `track_id` defaults None
2. `inspect_model("models/*.pt")` returns family, task, format from `model.task` + metadata
3. Unknown task/family returns `"unknown"` — never guesses from filename alone without dry infer fallback chain
4. Public API functions importable from `detect_only_v4` package
5. No imports from hex_detector, block_detected*, or legacy modules

**Depends on:** —  
**Blocks:** Phases 4, 5, 6

---

## Phase 4: Model Discovery & Formats

**Goal:** Auto-scan `models/` for all supported formats with Pi-aware backend priority and platform gates.

**Requirements:** MODEL-01, MODEL-02, MODEL-03, MODEL-04, MODEL-05

**Deliverables:**

- `src/detect_only_v4/models/loader.py` — load_model(), discover_models()
- `src/detect_only_v4/models/backends/` — pytorch, onnx, ncnn, tflite, tensorrt stub
- `src/detect_only_v4/models/priority.py` — NCNN > OpenVINO > ONNX > TFLite > PT
- Discovery cache with mtime invalidation

**Success criteria:**

1. `discover_models()` lists `.pt`, `.onnx`, `.tflite`, `.engine`, NCNN directories in `models/`
2. `load_model()` loads `.pt` on dev machine; returns LoadedModel handle
3. On Pi (or simulated), NCNN dir selected over `.pt` when both exist for same stem
4. `.engine` on Pi returns explicit unsupported error, not cryptic TensorRT crash
5. Unit tests: one fixture per format with mock/skip for missing weights

**Depends on:** Phase 3  
**Blocks:** Phases 5, 7, 8

---

## Phase 5: Task Adapters & Overlay

**Goal:** Normalize all Ultralytics task outputs into `DetectionResult` and render task-aware overlays.

**Requirements:** ADPT-01, ADPT-02, ADPT-03, ADPT-04, ADPT-05, ADPT-06, ADPT-07, ADPT-08

**Deliverables:**

- `src/detect_only_v4/detectors/{detect,segment,pose,obb}/adapter.py`
- `src/detect_only_v4/detectors/registry.py` — task → adapter
- `src/detect_only_v4/detectors/base.py` — shared helpers
- `src/detect_only_v4/render/overlay.py` + `render/drawers/`
- `detect_frame()` in pipeline module (sync, still-image capable)

**Success criteria:**

1. `normalize_results(raw, "detect")` returns list[DetectionResult] from mock Ultralytics Results
2. Segment adapter includes JSON-safe mask data
3. Pose adapter includes keypoints array; OBB adapter includes angle/corners
4. `track_id` always None — no tracker invoked
5. `draw_overlay` renders boxes/masks/keypoints/OBB per task without mutating input frame
6. Golden-frame unit tests per task adapter

**Depends on:** Phases 3, 4  
**Blocks:** Phases 7, 8

---

## Phase 6: Camera Discovery & Backends

**Goal:** Auto-detect cameras with native resolution/FPS probing and Pi-specific backends.

**Requirements:** CAM-01, CAM-02, CAM-03, CAM-04, CAM-05, CAM-06

**Deliverables:**

- `src/detect_only_v4/cameras/discovery.py` — discover_cameras(), probe_camera()
- `src/detect_only_v4/cameras/opencv.py`, `v4l2.py`, `picamera2.py`
- `src/detect_only_v4/cameras/factory.py` — backend selection
- Platform detect helper (Pi vs desktop)

**Success criteria:**

1. `discover_cameras()` returns list with id, backend, label on desktop (V4L2/USB)
2. `probe_camera()` reports actual width/height/fps after open — not requested defaults
3. Resolution change with safe fallback when rejected
4. Picamera2 backend optional import — graceful skip on non-Pi
5. Warmup discards first N frames; logs actual camera configuration

**Depends on:** Phase 3  
**Blocks:** Phases 7, 8

**Note:** Can parallelize with Phase 4–5 after Phase 3 complete.

---

## Phase 7: Threaded Pipeline

**Goal:** Realtime Pi-ready capture/inference with bounded queue and drop-old-frame policy.

**Requirements:** PIPE-01, PIPE-02, PIPE-03, PIPE-04, PIPE-05, PIPE-06

**Deliverables:**

- `src/detect_only_v4/pipeline/session.py` — InferenceSession orchestrator
- `src/detect_only_v4/pipeline/queue.py` — BoundedFrameQueue
- `src/detect_only_v4/pipeline/capture.py` — CaptureThread
- `src/detect_only_v4/pipeline/worker.py` — InferenceWorker
- `src/detect_only_v4/pipeline/metrics.py`
- Sync CLI loop via `__main__.py` (optional dev path)

**Success criteria:**

1. Capture thread runs independently; inference never blocks camera read
2. Queue maxsize=1 with drop-old verified in unit test
3. Inference error logs and skips frame — camera continues
4. SessionSnapshot readable under lock with latest overlay + DetectionResult list
5. Metrics expose capture_fps, infer_fps, dropped_frames, infer_ms

**Depends on:** Phases 4, 5, 6  
**Blocks:** Phase 8

---

## Phase 8: FastAPI WebSocket UI

**Goal:** LAN-accessible Web UI for model/camera selection, live preview, and runtime tuning.

**Requirements:** WEB-01, WEB-02, WEB-03, WEB-04, WEB-05, WEB-06, WEB-07, WEB-08

**Deliverables:**

- `src/detect_only_v4/api/app.py` — FastAPI factory + lifespan
- `src/detect_only_v4/api/routes/` — cameras, models, config, health
- `src/detect_only_v4/api/websocket.py` — /ws/stream
- `src/detect_only_v4/api/schemas.py` — Pydantic DTOs
- `src/detect_only_v4/static/index.html` — minimal control panel

**Success criteria:**

1. REST lists cameras and models with family/task/format metadata
2. WebSocket streams JPEG + JSON detections at capped rate
3. UI shows resolution, FPS, latency, model info
4. Runtime config patch (conf, IoU, imgsz, class filter) applies on next infer tick
5. Model/camera switch drains and reloads with warming_up status
6. HTTP endpoints remain responsive during active WebSocket stream

**Depends on:** Phase 7  
**Blocks:** Phase 9

---

## Phase 9: Pi Optimization & Hardening

**Goal:** Production-ready Pi 5 deployment with NCNN priority, full test suite, and documentation.

**Requirements:** QA-01, QA-02, QA-03, QA-04, QA-05

**Deliverables:**

- NCNN/OpenVINO priority validation on Pi (or documented manual gate)
- `tests/detect_only_v4/` complete suite
- README with Pi install, NCNN export, Web UI usage
- `pyproject.toml` `[detect-only-v4]` extra + entry point
- Optional `main.py --detect-only-v4` launcher flag

**Success criteria:**

1. All public API functions have type hints
2. CI runs adapter/discovery/queue tests without hardware
3. README documents apt packages + venv --system-site-packages
4. Benchmark table logged on NCNN vs PT load (Pi manual verification noted)
5. `python -m detect_only_v4` starts Web UI successfully

**Depends on:** Phase 8  
**Blocks:** Milestone v2.0 ship

---

## Parallelization Notes

```
Phase 3 (Core)
    ├── Phase 4 (Models) ──┐
    ├── Phase 5 (Adapters) ──┼── Phase 7 (Pipeline) ── Phase 8 (Web) ── Phase 9 (Hardening)
    └── Phase 6 (Cameras) ──┘
```

Phases 4, 5, 6 can start after Phase 3; Phase 7 requires 4+5+6; Phase 8 requires 7.

**MVP demo path:** 3 → 4 → 5 (detect only) → 6 → 7 → 8 → 9

---

## Milestone v2.0 Success Definition

Milestone v2.0 ships when:

- All 42 requirements marked Complete in traceability
- Phases 3–9 verified
- Pi 5 manual validation documented (NCNN inference + Picamera2 or USB camera)
- Greenfield constraint verified: zero imports from legacy modules

---
*Roadmap created: 2026-07-03 for milestone v2.0*

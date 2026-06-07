# Roadmap: Block Detected

## Overview

Layered computer-vision Python package: webcam detection today; tracking and alternate backends later.

## Phases

- [x] **Phase 1: Package foundation** - Initial modular refactor (webcam working)
- [x] **Phase 2: CV layered folder structure** - Scalable folder layout, tests, docs
- [x] **Phase 3–6:** Runtime, PySide6 GUI, hardening, postprocess (verified — 76 tests)
- [ ] **Phase 7: Web telemetry API** - MJPEG/WS stream + metrics + log tail (unblock Stitch UI)
- [ ] **Phase 8: YOLO inference params** - imgsz, IoU, max_det, device + hot-reload API
- [ ] **Phase 9: Stability/reject spec** - margin, unknown class, HTML-aligned defaults
- [ ] **Phase 10: Camera & viewport** - source enum, fps/exposure/WB, coordDebug mapping
- [ ] **Phase 11: ROI & preprocess controls** - ROI crop stage + contrast/brightness/saturation
- [ ] **Phase 12: Classical CV pipeline** - blur/canny/contours/warp + overlay toggles
- [ ] **Phase 13: Primary target telemetry** - tracker FSM + kinematics JSON for bottom panel
- [ ] **Phase 14: Config profiles** - named profile CRUD + web config API

## Phase Details

### Phase 1: Package foundation
**Goal**: Webcam app runs from installable package with AGENTS.md
**Depends on**: Nothing
**Requirements**: REQ-01, REQ-02
**Success Criteria**:
  1. `python main.py` starts webcam inference
  2. Source under `src/block_detected/` (not one monolithic script)
  3. AGENTS.md maps modules to responsibilities
**Plans**: 1 plan (ad-hoc refactor)

Plans:
- [x] 01-01: Initial package refactor

### Phase 2: CV layered folder structure for scalable expansion
**Goal**: Layered folders (apps/config/core/detection/vision/io/ui), pytest foundation, synced docs
**Depends on**: Phase 1
**Requirements**: REQ-02, REQ-03
**Success Criteria**:
  1. Six layers present under `src/block_detected/` with dependency rules documented
  2. `pytest tests/` passes (pure modules)
  3. AGENTS.md + `.planning/codebase/` reflect current tree
**Plans**: 3 plans

Plans:
- [x] 02-01: Finalize layered tree + expansion stubs
- [x] 02-02: Pytest foundation
- [x] 02-03: Docs sync + verification

## Progress

| Phase | Plans Complete | Status | Completed |
|-------|----------------|--------|-----------|
| 1. Package foundation | 1/1 | Complete | 2026-06-02 |
| 2. CV layered structure | 3/3 | Complete | 2026-06-02 |
| 3. Runtime engine + config | 2/2 | Complete | 2026-06-07 |
| 4. Desktop GUI | 2/2 | Complete | 2026-06-07 |
| 5. GUI hardening / UAT | 2/2 | Complete | 2026-06-07 |
| 6. Postprocess + stability | 2/2 | Complete | 2026-06-07 |

### Phase 3: Runtime engine, typed config, and detector abstraction for GUI prep

**Goal:** Deliver `WebcamEngine` runtime loop (read → infer → postprocess → render → metrics), typed `AppConfig` with TOML load/save/validate, `DetectorBackend` protocol with YOLO loader, and hot-reload vs restart key classification — no GUI code; Phase 4 consumes engine only.

**Requirements**: REQ-02, REQ-04
**Depends on:** Phase 2
**Success Criteria:**
  1. `WebcamEngine.process_frame()` runs full loop; mocked tests pass without camera or `.pt` weights
  2. `AppConfig` defaults, TOML round-trip, validation, and `RESTART_CAMERA_KEYS` / `RESTART_DETECTOR_KEYS` classification tested
  3. `core/protocols.DetectorBackend` has no OpenCV/YOLO imports; engine uses `load_detector()` not direct Ultralytics
  4. Hot config (`apply_hot_config`, `config_apply`) updates stability without camera/detector restart
  5. `runtime/` modules (`engine`, `config_schema`, `config_store`, `metrics`, `state`) importable; pytest subset for Phase 3 passes
**Plans:** 2 plans (retroactive verify + close gaps)

Plans:
- [x] 03-01-PLAN.md — Config schema, store, and hot-reload test gaps + REQ-04
- [x] 03-02-PLAN.md — Engine process_frame, detector abstraction tests + phase verification

### Phase 4: Desktop GUI for webcam runtime control and config

**Goal:** PySide6 desktop GUI (`apps/gui/app.py`) as primary entry (`python main.py` / `block-detected`) delegating to `WebcamEngine` — start/stop, confidence/eval, camera/model controls, stability hot-reload, log panel via `get_log_lines()`, aspect-ratio preview.

**Requirements**: REQ-01, REQ-04
**Depends on:** Phase 3
**Success Criteria:**
  1. `MainWindow` loads and round-trips `AppConfig` controls offscreen; `main.py` and console script target `apps.gui.app.main`
  2. GUI reads logs only via `get_log_lines()`; worker uses `engine.shutdown(destroy_cv_windows=False)`
  3. Control groups present: Runtime, Inference, Stability, Camera, Config, log panel
  4. Manual smoke: Start/Stop preview, live conf/eval, model/camera cycle (webcam + weights)
**Plans:** 2 plans (retroactive verify + close gaps)

Plans:
- [x] 04-01-PLAN.md — GUI control wiring, entry point, and log panel tests
- [x] 04-02-PLAN.md — 04-VERIFICATION.md + manual preview smoke checkpoint

### Phase 5: GUI and runtime hardening for production UAT

**Goal:** Harden GUI worker lifecycle for production UAT — run-generation guards, stop-pending UX, restart-required hints, error surfacing; align `05-UAT.md` with automated evidence.

**Requirements**: REQ-01, REQ-04
**Depends on:** Phase 4
**Success Criteria:**
  1. Stale `frame_ready`/`error` signals ignored via `_run_generation` (tested)
  2. `frame_thread` cleared only after `finished` or successful `wait()`; Start disabled while stopping
  3. Restart-only fields disabled while running; hint shown when camera/model edits pending
  4. `python -m pytest tests/ -q` passes; manual 05-UAT checklist completed on hardware
**Plans:** 2 plans (retroactive verify + close gaps)

Plans:
- [x] 05-01-PLAN.md — test_gui_hardening: generation guards, stop-pending, restart hints
- [x] 05-02-PLAN.md — 05-VERIFICATION.md, UAT doc alignment, production UAT checkpoint

### Phase 6: Detection post-processing, reject rules, and temporal stability

**Goal:** Post-inference spatial filters and temporal stability in `runtime/postprocess.py` wired into `WebcamEngine` when `stability.enabled`; GUI/TOML controls; full pytest coverage of reject paths and hot-reload.

**Requirements**: REQ-01, REQ-04
**Depends on:** Phase 5
**Success Criteria:**
  1. Filters: min confidence, min area, edge reject, duplicate merge IoU, temporal vote window — each tested
  2. `DetectionPostProcessor.update_config` rebuilds tracker on window/votes/IoU change; reset when disabled
  3. `process_frame` applies postprocess; `detection_count` reflects filtered output (engine test)
  4. Manual webcam: stability reduces flicker; TOML persistence (Phase 9 adds margin/unknown)
**Plans:** 2 plans (retroactive verify + close gaps)

Plans:
- [x] 06-01-PLAN.md — update_config + engine postprocess integration tests
- [x] 06-02-PLAN.md — 06-VERIFICATION.md finalize + optional manual stability UAT

### Phase 7: Web telemetry API and frame streaming for Stitch console

**Goal:** HTTP backend exposing `WebcamEngine` to Stitch `code.html` — MJPEG frame stream, engine control, metrics JSON, log tail.
**Ref:** `BACKEND_GAP_ANALYSIS.md` §4.2, §4.4, mapping "Top nav / Viewport / Main feed"
**Depends on:** Phase 6
**Requirements:** REQ-01, REQ-04
**Success Criteria:**
  1. `GET /stream` serves `multipart/x-mixed-replace` MJPEG from engine annotated frames; usable as `<img src="http://HOST:PORT/stream">`
  2. `POST /api/start`, `/api/stop`, `/api/camera/next`, `/api/model/next` wrap `WebcamEngine` methods (no duplicated detection/camera logic)
  3. `GET /api/telemetry` returns `{fps, latency_ms, render_ms}` where `latency_ms = frame_read_ms + inference_ms`; `GET /api/logs?limit=N` tails `get_log_lines()`
  4. `runtime/api/` routes + schemas; `apps/web/server.py` entry; `pip install -e ".[web]"` + `block-detected-web`; `pytest tests/test_web_api.py` passes without camera
  5. Optional: static mount serves `example_ui/stitch_block_pickup_vision_console/` at `/ui` for local Stitch dev
**Plans:** 3 plans

Plans:
- [ ] 07-01-PLAN.md — EngineService frame loop, Pydantic schemas, FastAPI factory + CORS
- [ ] 07-02-PLAN.md — MJPEG `/stream` + POST control routes wired into app
- [ ] 07-03-PLAN.md — Telemetry/log endpoints, `[web]` deps, entry script, TestClient tests

### Phase 8: YOLO inference params expansion and hot-reload API

**Goal:** Extend `InferenceConfig` + `YoloDetector.predict()` for full sidebar §5.2 params; expose via web API.
**Ref:** `BACKEND_GAP_ANALYSIS.md` §2.1–2.3
**Depends on:** Phase 7
**Success Criteria:**
  1. Config: `imgsz`, `iou`, `max_det`, `device`, optional `class_names` override
  2. `YoloDetector.predict()` passes Ultralytics params; tests with mock backend
  3. Hot-reload conf + IoU via API (reuse `RESTART_*` / hot keys pattern)
  4. (Optional stub) ONNX backend placeholder in `detection/onnx/`
**Plans:** 0 plans

Plans:
- [ ] TBD (run /gsd-plan-phase 8 to break down)

### Phase 9: Stability and reject rules spec alignment

**Goal:** Align postprocess defaults with HTML spec; add margin/unknown reject rules.
**Ref:** `BACKEND_GAP_ANALYSIS.md` §4.1
**Depends on:** Phase 8
**Success Criteria:**
  1. `RejectConfig` or extend `StabilityConfig`: `top1_top2_margin`, `unknown_if_low_margin`
  2. Defaults: temporal_window=7, required_stable_votes=5, min_confidence=0.70
  3. UNKNOWN class emitted when margin too low; tests in `tests/test_postprocess.py`
  4. Web API exposes stability toggles (temporal smoothing checkbox ↔ `stability.enabled`)
**Plans:** 0 plans

Plans:
- [ ] TBD (run /gsd-plan-phase 9 to break down)

### Phase 10: Camera source types viewport and coordinate mapping

**Goal:** Camera adapter enum + viewport/coord model for web overlay alignment.
**Ref:** `BACKEND_GAP_ANALYSIS.md` §1.1–1.2
**Depends on:** Phase 9
**Success Criteria:**
  1. `cameraSource` enum: USB index, OBS virtual, Pi/libcamera adapter stub
  2. `fpsTarget`, `exposureLock`, `whiteBalanceLock` via OpenCV/platform props
  3. ViewportConfig: frame vs viewport dims, `objectFit`, `coordDebug` (scale, offsetX/Y)
  4. Coordinate map helpers in `vision/geometry.py` for frame ↔ viewport
**Plans:** 0 plans

Plans:
- [ ] TBD (run /gsd-plan-phase 10 to break down)

### Phase 11: ROI crop stage and preprocessing controls

**Goal:** ROI crop before infer + sidebar §5.1 color adjustments wired to engine.
**Ref:** `BACKEND_GAP_ANALYSIS.md` §1.3 item 4, §3.2 pre-processing sliders
**Depends on:** Phase 10
**Success Criteria:**
  1. `RoiConfig` (x, y, width, height) + crop stage in engine loop
  2. Contrast/brightness/saturation applied pre-infer (OpenCV or numpy)
  3. Web sidebar binds ROI + preprocess sliders; hot-reload where safe
  4. Default resolution option 640×480 aligned with spec
**Plans:** 0 plans

Plans:
- [ ] TBD (run /gsd-plan-phase 11 to break down)

### Phase 12: Classical CV pipeline and overlay layers

**Goal:** Implement `ClassicalPipelineConfig` stages + viewport overlay toggles (Contours/Corners/Warped Face).
**Ref:** `BACKEND_GAP_ANALYSIS.md` §3.1–3.3 (largest gap)
**Depends on:** Phase 11
**Success Criteria:**
  1. `vision/preprocess/` or `runtime/classical.py`: blur → canny/adaptive/hsv → morphology
  2. Contour find + filter (area, aspect, convex, approx) → candidate boxes
  3. Perspective warp + face patch (`warpSize`); reject internal contours
  4. Overlay render layers toggled by API flags; Canny/blur sidebar §5.3–5.4 wired
**Plans:** 0 plans

Plans:
- [ ] TBD (run /gsd-plan-phase 12 to break down)

### Phase 13: Primary target kinematics and tracker state machine

**Goal:** Domain types + tracker FSM for bottom telemetry panel (§4.1–4.2).
**Ref:** `BACKEND_GAP_ANALYSIS.md` §4.3
**Depends on:** Phase 12
**Success Criteria:**
  1. `PrimaryTarget` / `Kinematics` in `core/domain.py` emitted each frame
  2. Tracker FSM: acquired → tracking → lost
  3. Centroid, angle, pose fields populated for highest-confidence stable detection
  4. WebSocket telemetry payload includes primary detect + confidence bar data
**Plans:** 0 plans

Plans:
- [ ] TBD (run /gsd-plan-phase 13 to break down)

### Phase 14: Named config profiles and web config API

**Goal:** Multi-profile persistence + footer §6 controls for Stitch console.
**Ref:** `BACKEND_GAP_ANALYSIS.md` §4.4, mapping "Footer profiles"
**Depends on:** Phase 13
**Success Criteria:**
  1. Profile store: load/save/delete named TOML/JSON under `profiles/` or config dir
  2. API: list profiles, select active, SAVE CONFIG, DELETE profile
  3. Profile switch applies hot vs restart keys correctly
  4. Stitch `code.html` can bind dropdown + footer buttons to API (integration smoke test)
**Plans:** 0 plans

Plans:
- [ ] TBD (run /gsd-plan-phase 14 to break down)

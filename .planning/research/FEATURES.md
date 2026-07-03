# Feature Landscape

**Domain:** Modular YOLO inference platform on Raspberry Pi 5 (Detect Only v4)
**Researched:** 2026-07-03
**Scope:** NEW features in `src/detect_only_v4/` only — hex_detector geometry and dataset debugger are out of scope
**Overall confidence:** HIGH (stack choices verified via Ultralytics docs + existing repo patterns)

---

## Feature Behavior Reference

How each target feature typically works and what callers should expect.

### Model discovery & auto-identify

**Expected behavior:**

1. **Discovery** — Scan `models/` at repo root. Return a sorted list of loadable artifacts:
   - Single files: `*.pt`, `*.onnx`, `*.engine`, `*.tflite`
   - NCNN bundles: directories containing paired `.param` + `.bin` (Ultralytics convention: `{name}_ncnn_model/`)
2. **Format detection** — Infer from extension/path shape, not magic bytes. NCNN is a directory, not a file.
3. **Family identification** — Resolve YOLO generation from filename heuristics and/or loaded metadata:
   - `yolo26*`, `yolo11*`, `yolov8*`, `yolov5*` patterns in basename
   - Fallback: `model.model.yaml` / checkpoint metadata after lightweight load
   - Unknown family → `"unknown"` with load still attempted
4. **Task identification** — Resolve task before or during load:
   - Filename suffixes: `-seg` → segment, `-pose` → pose, `-obb` → obb; default → detect
   - After `YOLO(path)`: read `model.task` (Ultralytics sets this from checkpoint/ONNX metadata)
   - Supported in-scope tasks: **detect, segment, pose, obb** (classify/semantic explicitly out of scope per PROJECT.md)
5. **Pi priority** — When multiple formats exist for the same logical model, prefer NCNN > ONNX > TFLite > PT for inference selection hints (not auto-delete others).

**Returns:** `ModelDescriptor(path, format, family, task, display_name, loadable: bool, error?: str)`.

**Failure modes:** Missing `models/`, empty scan, corrupt file → descriptor with `loadable=False` and reason; discovery itself never raises.

---

### Task adapters → normalized `DetectionResult`

**Expected behavior:**

Each Ultralytics task exposes different `Results` fields. Adapters map raw output → one canonical `DetectionResult` per detected instance:

| Task | Raw Ultralytics fields | Normalized fields |
|------|------------------------|-------------------|
| detect | `boxes.xyxy`, `cls`, `conf`, `names` | `bbox_xyxy`, `class_id`, `class_name`, `confidence` |
| segment | `boxes` + `masks.data` / `masks.xy` | above + `mask_polygon` or RLE ref (JSON-safe) |
| pose | `boxes` + `keypoints.xy`, `keypoints.conf` | above + `keypoints: [{x,y,conf}, ...]` |
| obb | `obb.xyxyxyxy` or `obb.xywhr` | above + `obb_corners` or `center, w, h, angle` |

**Contract rules:**

- `normalize_results(raw, task)` is pure — no I/O, no mutation of input frame.
- Every result is JSON-serializable (`to_dict()` / dataclass → dict). No `ndarray` in wire format.
- **No tracking** — one `DetectionResult` per model output instance per frame; no `track_id` assignment.
- Adapter selected by resolved `task`, not by caller guess. Wrong adapter → explicit error, not silent empty list.
- Class names from `result.names` / model metadata; missing names fall back to stringified `class_id`.

---

### Core API functions

| Function | Input | Output | Expected behavior |
|----------|-------|--------|-------------------|
| `load_model` | path, optional `task` override | `LoadedModel` handle | `YOLO(str(path), task=...)`; lazy — no warmup infer unless configured. Raises on unloadable path. |
| `inspect_model` | path | `ModelInfo` | Metadata without holding camera or running inference: format, family, task, class names, stride/imgsz if available, file size. May do lightweight `YOLO` init; must not require GPU. |
| `discover_cameras` | — | `list[CameraInfo]` | Enumerate candidates: V4L2 `/dev/video*` indices, Picamera2 if Pi + importable. Each entry: `id`, `backend`, `label`. |
| `probe_camera` | camera id | `CameraCaps` | Open → read **actual** `width`, `height`, `fps` (not requested defaults) → grab 1–3 test frames → release. `opened: bool`, `native_resolution`, `actual_fps`, `backend`. |
| `detect_frame` | model, frame (ndarray), `InferConfig` | raw Ultralytics `Results` | Single `model(frame, conf=..., iou=..., imgsz=..., max_det=..., verbose=False)`. No overlay, no normalize. |
| `normalize_results` | raw results, task | `list[DetectionResult]` | Delegates to task adapter. Empty list if nothing detected. |
| `draw_overlay` | frame, results, `DrawConfig` | annotated ndarray | Task-aware boxes/masks/keypoints/OBB; optional labels, conf text, FPS watermark. Does not mutate input frame (copy-on-draw). |

**Design intent:** Library-first API — FastAPI UI and future robot/telemetry consumers call the same functions. No hidden global state inside API layer (pipeline may hold state separately).

---

### Camera auto-detect (native resolution / FPS)

**Expected behavior:**

1. **Platform branch** — On Pi (`/proc/device-tree/model` or equivalent): try Picamera2 → libcamera → V4L2 USB. On desktop: V4L2 index scan only.
2. **Discovery** — `discover_cameras()` probes indices `0..N` (N≈10); skip nodes that open but return empty frames.
3. **Native caps** — `probe_camera` opens without forcing resolution first, reads `CAP_PROP_FRAME_WIDTH/HEIGHT/FPS` (or Picamera2 sensor modes), then reports **actual** values after optional `set()` round-trip.
4. **Latency defaults** — V4L2: `CAP_PROP_BUFFERSIZE=1`, prefer MJPEG fourcc when available (pattern from existing `stream/server.py`).
5. **Stable IDs** — Camera identity is `(backend, index_or_path)` tuple, not display order alone.

**Not expected:** Auto-exposure tuning, autofocus control, or multi-camera sync — out of scope for v2.0.

---

### FastAPI + WebSocket UI (runtime config)

**Expected behavior:**

**REST (bootstrap):**

- `GET /health` — pipeline alive, model loaded, camera open, last frame age
- `GET /models` — `discover_models()` merged with active selection
- `GET /cameras` — `discover_cameras()` merged with active selection
- `POST /config` or WS-only config — apply `InferConfig` patch (conf, iou, imgsz, max_det, model_path, camera_id)

**WebSocket (live loop):**

- Client connects → server pushes periodic messages (~15–30 Hz cap, not raw camera FPS)
- **Outbound message shape:** `{ type: "frame", ts, detections: [...], stats: {fps, infer_ms}, jpeg_b64? }` or split binary JPEG + JSON metadata channel
- **Inbound:** `{ type: "config", patch: { conf: 0.5, ... } }`, `{ type: "select_model", path }`, `{ type: "select_camera", id }`
- Config changes apply on **next inference tick** — no mid-forward interrupt required
- Model/camera switch: drain pipeline, release resource, reload, resume (brief `warming_up` status)

**Runtime constraints:**

- Single Uvicorn worker — camera and model are process-singletons
- FastAPI `lifespan` starts/stops inference pipeline thread on app boot/shutdown
- CORS open for LAN dev; no auth in v2.0 MVP

**UI table stakes:** model dropdown, camera dropdown, live preview, detection JSON panel, sliders for conf/IoU/imgsz.

---

### Pi 5 optimization (bounded queue, drop-old-frame, inference thread)

**Expected behavior:**

```
[Capture Thread] --drop-old--> [frame_q maxsize=1] --> [Inference Thread] --> [latest_result lock]
                                                                              --> WebSocket / REST
```

1. **Capture thread** — Continuous `read()`; if `frame_q.full()`, `get_nowait()` then `put` (always newest frame).
2. **Inference thread** — Blocks on `frame_q.get()`; runs `detect_frame` → `normalize_results` → `draw_overlay`; writes atomically to `LatestResult` holder.
3. **Queue depth** — `maxsize=1` (recommended) or `2` max; never unbounded.
4. **No blocking capture** — Slow inference drops frames, never stalls camera driver.
5. **NCNN priority** — On Pi, `load_model` prefers `.ncnn_model` directory when multiple formats match; log when falling back to PT.
6. **Metrics** — Expose `capture_fps`, `infer_fps`, `dropped_frames`, `infer_ms` in UI/stats.

**Not expected:** Multiprocessing, SharedMemory optimization, or Coral/Hailo backends in v2.0.

---

## Table Stakes

Features users expect. Missing = product feels incomplete.

| Feature | Why Expected | Complexity | Notes |
|---------|--------------|------------|-------|
| Model scan in `models/` | Without it, user must hardcode paths | Low | Extend beyond `.pt` — ONNX/NCNN/TFLite/engine |
| `load_model` + `detect_frame` | Core purpose of the module | Med | Ultralytics `YOLO()` unified loader |
| Task-aware `normalize_results` | JSON consumers need stable schema | Med | Adapter per task; detect first |
| `draw_overlay` on frame | Visual confirmation on Pi and in browser | Med | Reuse OpenCV/Ultralytics plot patterns |
| Camera enumeration + open | "Point at Pi and run" — no manual `/dev/video0` | Med | V4L2 scan + Picamera2 on Pi |
| `probe_camera` native caps | Wrong resolution silently kills FPS on Pi | Low | Report actual, not requested |
| Web UI live preview | PROJECT.md names Web UI as primary surface | High | MJPEG or WS JPEG + JSON |
| Runtime conf/IoU/imgsz change | Tuning without restart is standard for CV apps | Med | Thread-safe config holder |
| Model/camera switch from UI | Multi-model repo already exists | Med | Requires pipeline drain/reload |
| Structured logging | Robot integration and field debug | Low | stdlib `logging`, per-stage timings |
| Type hints + dataclasses | PROJECT.md requirement; enables IDE + tests | Low | All public API typed |
| Unit tests for adapters/API | Greenfield module needs contract tests | Med | Mock `Results`, no camera in CI |

---

## Differentiators

Features that set the product apart. Not universally expected, but high value for this project.

| Feature | Value Proposition | Complexity | Notes |
|---------|-------------------|------------|-------|
| Multi-format model discovery | Same API for `.pt`, ONNX, NCNN, TFLite, engine | Med | NCNN priority on Pi is a deliberate perf choice |
| Auto-identify family + task | User drops weights in `models/` — no YAML | Med | Heuristics + `model.task` fallback |
| Unified `DetectionResult` across 4 tasks | Downstream robot code writes once | High | Main architectural bet |
| Library-first API under FastAPI | Embeddable without web server | Med | Unlike stream-only JPEG server |
| Drop-old-frame pipeline | Actually realtime on Pi 5 CPU | Med | Distinct from v1 synchronous `process_single_frame` |
| LAN WebSocket config + telemetry | Headless Pi operated from laptop | High | Extends `stream/` discovery idea with control plane |
| `inspect_model` without infer | Fast startup diagnostics in UI | Low | Useful for large model folders |

---

## Anti-Features

Features to explicitly NOT build.

| Anti-Feature | Why Avoid | What to Do Instead |
|--------------|-----------|-------------------|
| Object tracking / ByteTrack | PROJECT.md: always return all detections, no tracker | Raw per-frame instances only |
| Training / fine-tune | Out of scope; models exist | Document export-to-NCNN workflow in README |
| hex_detector merge | Separate milestone | Keep `detect_only_v4` greenfield |
| GPU / CUDA on Pi | Hardware not available | NCNN + CPU ONNX |
| Multi-worker Uvicorn | Camera/model singleton conflict | `--workers 1` |
| Unbounded frame queue | Latency snowball on Pi | `Queue(1)` drop-old |
| Desktop OpenCV GUI as primary | PROJECT.md: FastAPI is main surface | Optional dev script only, not shipped UX |
| Auth / multi-tenant | LAN lab tool, not SaaS | Defer; document bind `0.0.0.0` risk |
| Classify / semantic segmentation | Active scope is detect/segment/pose/obb | Reject or `unsupported_task` in inspect |
| Auto model download | Offline Pi, local `models/` only | Fail with clear message |
| Recording / clip export | Scope creep | Defer post-MVP |

---

## Feature Dependencies

```
models/ directory layout
    └── model discovery
            └── auto-identify (family, task)
                    └── load_model
                            └── inspect_model (partial — can run without load)

discover_cameras
    └── probe_camera
            └── pipeline capture thread

load_model + task resolution
    └── task adapter registry
            └── normalize_results
                    └── draw_overlay

detect_frame
    └── normalize_results (via task)
    └── draw_overlay (optional)

InferConfig (dataclass)
    └── detect_frame
    └── runtime config (UI)

pipeline (queues + threads)
    └── detect_frame + normalize + draw
    └── FastAPI /health, /stream, WebSocket

FastAPI lifespan
    └── pipeline start/stop
    └── WebSocket push loop
```

**Critical path for MVP:** model discovery → load_model → detect_frame → normalize (detect adapter) → draw_overlay → single camera open → manual CLI or minimal API.

**Parallel path after MVP:** full task adapters → WebSocket UI → Pi queue optimization → NCNN priority.

---

## MVP Recommendation

**Goal:** Prove end-to-end inference on Pi (or dev machine) with stable JSON contract — without full Web UI polish.

### Prioritize (MVP)

1. **Dataclasses** — `DetectionResult`, `ModelInfo`, `CameraInfo`, `InferConfig`, `DrawConfig`
2. **Model discovery** — `.pt` + NCNN directory; family/task from filename + `model.task`
3. **`load_model`, `inspect_model`, `detect_frame`, `normalize_results` (detect only), `draw_overlay` (boxes only)**
4. **`discover_cameras`, `probe_camera`** — V4L2 first; Picamera2 stub or full on Pi
5. **Synchronous CLI entry** — `python -m detect_only_v4` runs camera loop in main thread (validates API before threading)
6. **Unit tests** — adapter detect, model inspect mocks, discovery on fixture dir

### Phase 2 (immediately after MVP)

7. **Inference thread + bounded queue** — drop-old-frame
8. **FastAPI** — `/health`, `/models`, `/cameras`, WebSocket with JPEG + JSON
9. **Runtime config** — conf/IoU/imgsz via WS patch
10. **Remaining task adapters** — segment, pose, obb

### Defer

| Feature | Reason |
|---------|--------|
| `.engine` / `.tflite` load paths | Lower priority on Pi; add after NCNN+ONNX stable |
| Binary WS split (JPEG separate from JSON) | Base64 in JSON sufficient for MVP LAN |
| Model hot-swap without brief pause | Accept `warming_up` gap in v2.0 |
| Frontend polish (themes, persistence) | Functional > pretty |
| SharedMemory queue | Optimize only if profiling shows Queue bottleneck |

---

## Prioritization Matrix

Scoring: **Impact** (1–5), **Effort** (1–5, higher = more work), **Risk** (1–5). **Priority = Impact / (Effort × Risk)** — qualitative bucket: P0 (now), P1 (next), P2 (later).

| Feature | Impact | Effort | Risk | Bucket | Rationale |
|---------|--------|--------|------|--------|-----------|
| Core dataclasses + detect adapter | 5 | 2 | 1 | **P0** | Foundation for all consumers |
| Model discovery `.pt` + NCNN | 5 | 2 | 2 | **P0** | Unblocks real Pi models |
| `load_model` / `detect_frame` | 5 | 2 | 2 | **P0** | Core value |
| Camera discover + probe (V4L2) | 4 | 3 | 2 | **P0** | Can't demo without camera |
| `draw_overlay` detect | 4 | 2 | 1 | **P0** | Visual validation |
| Unit tests (adapters, discovery) | 4 | 2 | 1 | **P0** | Greenfield quality gate |
| Bounded queue + infer thread | 5 | 3 | 3 | **P1** | Required for realtime Pi; depends on P0 API |
| FastAPI REST bootstrap | 4 | 2 | 2 | **P1** | UI foundation |
| WebSocket live stream | 5 | 4 | 3 | **P1** | Primary UX per PROJECT.md |
| Runtime config hot-reload | 4 | 3 | 2 | **P1** | Expected in tuning workflow |
| Model/camera switch from UI | 3 | 3 | 3 | **P1** | Important but not day-1 |
| Auto-identify family/task | 3 | 3 | 3 | **P1** | Heuristics need edge-case tests |
| Segment adapter | 3 | 3 | 2 | **P2** | After detect path proven |
| Pose adapter | 3 | 3 | 2 | **P2** | Keypoint schema decisions |
| OBB adapter | 2 | 3 | 3 | **P2** | Niche for block project |
| ONNX + TFLite + engine discovery | 3 | 3 | 3 | **P2** | Format matrix expansion |
| Picamera2 native path | 4 | 4 | 4 | **P1** on Pi / **P2** on desktop | Pi-only; high integration risk |
| README + export NCNN guide | 3 | 1 | 1 | **P1** | Ops doc for Pi deploy |

---

## Complexity Summary

| Area | Overall | Main driver |
|------|---------|-------------|
| Model discovery + identify | Medium | Multi-format + heuristic edge cases |
| Task adapters | Medium–High | 4 tasks, JSON-safe masks/keypoints |
| Core API | Low–Medium | Thin Ultralytics wrapper if scoped |
| Camera layer | Medium | Pi vs desktop branching |
| Pi pipeline | Medium | Threading + drop-frame correctness |
| FastAPI WebSocket UI | High | Async + thread bridge + resource lifecycle |

---

## Sources

| Source | Confidence | Used for |
|--------|------------|----------|
| [Ultralytics Predict docs](https://docs.ultralytics.com/modes/predict/) | HIGH | Results fields per task (boxes, masks, keypoints, obb) |
| [Ultralytics Raspberry Pi guide](https://docs.ultralytics.com/guides/raspberry-pi/) | HIGH | NCNN export/load, Pi inference path |
| [Ultralytics NCNN integration](https://docs.ultralytics.com/integrations/ncnn/) | HIGH | NCNN folder format, supported tasks |
| [FastAPI WebSockets](https://fastapi.tiangolo.com/advanced/websockets/) | HIGH | WS accept/send_json pattern |
| [Ultralytics issue #19210](https://github.com/ultralytics/ultralytics/issues/19210) | MEDIUM | Queue(1) drop-old-frame pattern |
| `src/block_detected_v1/` (loader, boxes, engine, v4l2) | HIGH | Existing repo conventions to diverge from |
| `src/stream/server.py` | HIGH | V4L2 MJPEG, `CAP_PROP_BUFFERSIZE`, discovery |
| `.planning/PROJECT.md` | HIGH | Scope, anti-features, API names |

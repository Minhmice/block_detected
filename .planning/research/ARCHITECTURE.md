# Architecture Patterns

**Domain:** Modular YOLO inference platform on Raspberry Pi 5 with Web UI  
**Project:** Detect Only v4 (milestone v2.0)  
**Researched:** 2026-07-03  
**Overall confidence:** HIGH (requirements locked in PROJECT.md; Ultralytics/FastAPI patterns verified via official docs)

## Recommended Architecture

Detect Only v4 is a **layered greenfield module** (`src/detect_only_v4/`) with a **library core** (types, loaders, adapters, pipeline, render) and a **thin FastAPI shell** (REST + WebSocket). All realtime work runs off the asyncio event loop in dedicated threads; the API layer only reads the latest snapshot and pushes encoded frames/JSON to clients.

**Design principle:** One normalized contract (`DetectionResult`) at the center; everything else is a replaceable adapter.

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                         FastAPI App (async shell)                           │
│  REST: /cameras /models /config /health    WebSocket: /ws/stream            │
│  Serves: latest JPEG overlay + JSON DetectionResult snapshot                │
└───────────────────────────────┬─────────────────────────────────────────────┘
                                │ read lock / snapshot only (no inference here)
┌───────────────────────────────▼─────────────────────────────────────────────┐
│                    InferenceSession (orchestrator)                          │
│  owns: selected camera, loaded model, runtime config, metrics               │
│  API: start() stop() switch_model() switch_camera() get_snapshot()          │
└───────┬───────────────────────────────┬───────────────────────────────────┘
        │                               │
┌───────▼────────┐              ┌───────▼──────────────────────────────────┐
│ CaptureThread  │              │ InferenceWorker (daemon thread)            │
│ read frame     │──enqueue──▶  │ bounded queue (maxsize=1, drop-old)        │
│ probe metadata │   FramePkt  │ dequeue → predict → normalize → overlay    │
└───────┬────────┘              └───────┬──────────────────────────────────┘
        │                                 │
┌───────▼────────┐              ┌───────▼──────────────────────────────────┐
│ CameraBackend  │              │ ModelRuntime + TaskAdapter                 │
│ OpenCV/V4L2    │              │ loader backends → Ultralytics predict      │
│ Picamera2      │              │ detect/segment/pose/obb → DetectionResult  │
└────────────────┘              └────────────────────────────────────────────┘
```

### Component Boundaries

| Component | Responsibility | Communicates With |
|-----------|---------------|-------------------|
| `core/types` | `DetectionResult`, `FramePacket`, `ModelInfo`, `CameraInfo`, `TaskKind` | All layers |
| `core/protocols` | `CameraBackend`, `ModelBackend`, `TaskAdapter` ABCs | loaders, adapters, pipeline |
| `models/loader` | Discover paths, pick backend by extension, `load_model()` | `models/backends/*`, inspector |
| `models/inspector` | `inspect_model()` — family, task, classes, input size, format | loader, API |
| `models/backends` | `.pt`, `.onnx`, `.engine`, `.tflite`, NCNN dir | Ultralytics / runtime libs |
| `detectors/{detect,segment,pose,obb}/` | Map Ultralytics `Results` → `DetectionResult` | `normalize_results`, render |
| `cameras/` | `discover_cameras`, `probe_camera`, backend factory | OpenCV, V4L2, Picamera2 |
| `pipeline/session` | Lifecycle, config apply, snapshot for API | capture thread, worker |
| `pipeline/queue` | Bounded queue, drop-old-frame policy | capture → worker |
| `pipeline/worker` | `detect_frame` loop, timing metrics | model runtime, adapters |
| `render/overlay` | Task-aware `draw_overlay(frame, result)` | OpenCV drawing |
| `api/app` | FastAPI routes, static UI, WS broadcast | `InferenceSession` only |
| `config/` | Defaults, schema, runtime overrides | session, API |

### Data Flow

**Cold start (discovery):**

```
models/ scan ──▶ loader.discover() ──▶ inspector.inspect() ──▶ ModelInfo[]
platform probe ──▶ cameras.discover() ──▶ probe_camera() ──▶ CameraInfo[]
```

**Hot path (one frame):**

```
CameraBackend.read()
  → FramePacket { ndarray BGR, timestamp, camera_id }
  → BoundedQueue.put_latest()     # drops stale if worker busy
  → worker: ModelRuntime.predict(frame)
  → Ultralytics Results (task-specific tensors)
  → TaskAdapter.normalize(results) → DetectionResult (JSON-serializable)
  → draw_overlay(frame, DetectionResult, task) → annotated ndarray
  → SessionSnapshot { jpeg_bytes, DetectionResult, fps, latency_ms }
  → WebSocket clients / REST poll
```

**DetectionResult contract (hub type):**

| Field | detect | segment | pose | obb |
|-------|--------|---------|------|-----|
| `task` | ✓ | ✓ | ✓ | ✓ |
| `boxes[]` xyxy + conf + cls | ✓ | ✓ (instance) | ✓ (person bbox) | — |
| `masks[]` or RLE | — | ✓ | — | — |
| `keypoints[]` | — | — | ✓ | — |
| `obb[]` cxcywh + angle | — | — | — | ✓ |
| `meta` timing, model_id, frame_size | ✓ | ✓ | ✓ | ✓ |

Adapters own task-specific population; overlay and JSON export read only `DetectionResult`.

## Recommended Project Structure

```
src/detect_only_v4/
├── __init__.py              # public API re-exports
├── __main__.py              # python -m detect_only_v4
├── core/
│   ├── types.py             # DetectionResult, FramePacket, ModelInfo, CameraInfo
│   ├── protocols.py         # CameraBackend, ModelBackend, TaskAdapter
│   └── errors.py            # typed exceptions / error codes
├── config/
│   ├── defaults.py
│   ├── schema.py            # dataclasses: RuntimeConfig, InferenceConfig
│   └── store.py             # load/save JSON (optional persistence)
├── models/
│   ├── loader.py            # load_model(), discover_models()
│   ├── inspector.py         # inspect_model() — family, task, classes
│   └── backends/
│       ├── base.py
│       ├── pytorch.py       # .pt
│       ├── onnx.py          # .onnx
│       ├── tensorrt.py      # .engine (stub/optional on Pi)
│       ├── tflite.py        # .tflite
│       └── ncnn.py          # *_ncnn_model/ directory (Pi priority)
├── detectors/
│   ├── registry.py          # task → adapter class
│   ├── base.py              # shared normalize helpers
│   ├── detect/adapter.py
│   ├── segment/adapter.py
│   ├── pose/adapter.py
│   └── obb/adapter.py
├── cameras/
│   ├── discovery.py         # discover_cameras(), probe_camera()
│   ├── factory.py           # build backend from CameraInfo + config
│   ├── opencv.py            # index / path capture
│   ├── v4l2.py              # CAP_V4L2, native res/FPS probe
│   └── picamera2.py         # Pi CSI via Picamera2
├── pipeline/
│   ├── session.py           # InferenceSession orchestrator
│   ├── queue.py             # BoundedFrameQueue (maxsize=1, drop-old)
│   ├── capture.py           # CaptureThread
│   ├── worker.py            # InferenceWorker thread
│   └── metrics.py           # fps, inference_ms, queue_drops
├── render/
│   ├── overlay.py           # draw_overlay() dispatcher
│   └── drawers/             # per-task drawing (boxes, masks, skeleton, obb)
├── api/
│   ├── app.py               # FastAPI factory, lifespan hooks
│   ├── routes/
│   │   ├── cameras.py
│   │   ├── models.py
│   │   ├── config.py
│   │   └── health.py
│   ├── websocket.py         # /ws/stream — JPEG + JSON envelope
│   └── schemas.py           # Pydantic request/response DTOs
└── static/                  # minimal HTML/JS client (optional phase)
    └── index.html
```

**Dependency rule (enforced):** `api` → `pipeline` → `{cameras, models, detectors, render}` → `core`. No upward imports.

## Patterns to Follow

### Pattern 1: Task Adapter Registry

**What:** Map inferred `TaskKind` to a single `TaskAdapter` implementation after `inspect_model()`.

**When:** Any code path that calls `predict()` must not branch on raw Ultralytics attributes in more than one place.

**Example:**

```python
# detectors/registry.py
ADAPTERS: dict[TaskKind, type[TaskAdapter]] = {
    TaskKind.DETECT: DetectAdapter,
    TaskKind.SEGMENT: SegmentAdapter,
    TaskKind.POSE: PoseAdapter,
    TaskKind.OBB: ObbAdapter,
}

def get_adapter(task: TaskKind) -> TaskAdapter:
    return ADAPTERS[task]()
```

Ultralytics already routes predictors by task (`result.boxes`, `.masks`, `.keypoints`, `.obb` per [official predict docs](https://docs.ultralytics.com/modes/predict/)). Adapters translate once into `DetectionResult`.

### Pattern 2: Format Backend Strategy

**What:** `ModelBackend` protocol with extension-based registration in `loader.py`.

**When:** Adding a new export format without touching pipeline or API.

| Extension / path | Backend | Pi 5 notes |
|------------------|---------|------------|
| `.pt` | `pytorch` | Dev/fallback; heavier on ARM |
| `*_ncnn_model/` dir | `ncnn` | **Default on Pi** per Ultralytics Pi guide |
| `.onnx` | `onnx` | Secondary export path |
| `.tflite` | `tflite` | Optional edge path |
| `.engine` | `tensorrt` | Out of scope on Pi (no CUDA); stub for API completeness |

`inspect_model()` runs lightweight probes (metadata, one dry forward or header parse) — not full discovery scan on every frame.

### Pattern 3: Producer–Consumer with Drop-Old-Frame

**What:** Capture thread enqueues into `queue.Queue(maxsize=1)`. On full queue, discard pending frame and insert newest.

**When:** Realtime preview on Pi where inference slower than camera FPS.

**Why:** Prevents latency spiral; matches PROJECT.md Pi 5 optimization requirement. Worker always processes the freshest frame.

```python
def put_latest(self, packet: FramePacket) -> None:
    try:
        self._q.put_nowait(packet)
    except queue.Full:
        try:
            self._q.get_nowait()  # drop stale
        except queue.Empty:
            pass
        self._q.put_nowait(packet)
```

### Pattern 4: Snapshot for Async Consumers

**What:** Worker writes `SessionSnapshot` under `threading.Lock`. FastAPI handlers copy the snapshot — never call `predict()` in route handlers.

**When:** WebSocket loop, REST `/snapshot`, config endpoints.

**WebSocket envelope (recommended):**

```json
{
  "type": "frame",
  "ts": 1719999999.123,
  "jpeg_b64": "...",
  "result": { /* DetectionResult */ },
  "metrics": { "fps": 12.4, "inference_ms": 78 }
}
```

Send JSON metadata every frame; JPEG can be throttled (e.g. 15–30 FPS) independently of inference rate.

### Pattern 5: Task-Aware Overlay Dispatcher

**What:** `draw_overlay(frame, result: DetectionResult) -> ndarray` delegates to per-task drawer based on `result.task`.

**When:** Any visual output — preview, WebSocket, future robot debug feed.

**Rule:** Overlay reads `DetectionResult` only, not raw Ultralytics `Results`. Keeps render testable without loading weights.

### Pattern 6: Camera Backend Factory

**What:** `discover_cameras()` returns unified `CameraInfo` list; `probe_camera(id)` fills native resolution/FPS; factory picks implementation.

| Source kind | Backend | Selection signal |
|-------------|---------|------------------|
| USB index | `opencv` / `v4l2` | Linux + V4L2 available → prefer V4L2 |
| CSI / libcamera | `picamera2` | `is_raspberry_pi()` + Picamera2 import ok |
| Fallback | `opencv` | Desktop dev, Windows |

`probe_camera()` must not start the inference pipeline — only open, read one frame, query caps, close.

## Anti-Patterns to Avoid

### Anti-Pattern 1: Inference on the Event Loop

**What:** Calling `model.predict()` or `cap.read()` inside `async def` route handlers.

**Why bad:** Blocks Uvicorn; WebSocket backpressure stalls entire server.

**Instead:** Worker thread + snapshot pattern; asyncio only for I/O and WS send.

### Anti-Pattern 2: Ultralytics Types Leaking Past Adapters

**What:** Passing `Results`, `Boxes`, torch tensors to API, overlay, or tests.

**Why bad:** Ties robot/telemetry consumers to Ultralytics; breaks non-PyTorch backends.

**Instead:** Normalize immediately in worker; downstream code sees only `DetectionResult`.

### Anti-Pattern 3: Monolithic Detector Class

**What:** One giant `detect_frame()` with `if task == "segment": ... elif pose: ...`.

**Why bad:** Un-testable, violates open/closed principle as tasks grow.

**Instead:** `detectors/{task}/adapter.py` + registry; shared math in `detectors/base.py`.

### Anti-Pattern 4: Blocking Queue Without Drop Policy

**What:** Unbounded queue or `maxsize>1` without drop-old.

**Why bad:** Latency grows unbounded when inference < camera FPS (common on Pi).

**Instead:** `maxsize=1` + drop-old explicitly counted in metrics.

### Anti-Pattern 5: Coupling to hex_detector or legacy runtime

**What:** Importing from `hex_detector`, `block_detected`, or `block_detected_v1`.

**Why bad:** Milestone scope violation; different domain (geometry vs YOLO tasks).

**Instead:** Duplicate only generic patterns (threading, logging style), not code. Integration is a future milestone.

### Anti-Pattern 6: Multi-Worker Uvicorn with Singleton Camera

**What:** `uvicorn --workers 4` with hardware camera.

**Why bad:** Multiple processes fight for `/dev/video0` or Picamera2 exclusive access.

**Instead:** Document `--workers 1` for Pi deployment; scale via LAN clients, not server workers.

## Integration Points

### New (this milestone — all under `src/detect_only_v4/`)

| Artifact | Purpose |
|----------|---------|
| Entire `src/detect_only_v4/` package | Greenfield module |
| `detect_only_v4` public API | `load_model`, `inspect_model`, `discover_cameras`, `probe_camera`, `detect_frame`, `normalize_results`, `draw_overlay` |
| FastAPI app + WebSocket | Primary UI surface |
| Unit tests `tests/detect_only_v4/` | Per-layer tests with mocked camera/model |

### Modified (repo integration — minimal, end of milestone)

| Artifact | Change | When |
|----------|--------|------|
| `pyproject.toml` | Add `fastapi`, `uvicorn`, optional `picamera2`, `[detect-only-v4]` extra, entry point `detect-only-v4 = detect_only_v4.__main__:main` | Phase: API packaging |
| `main.py` (optional) | Add `--detect-only-v4` launcher flag | Phase: launcher wiring |
| `models/` (read-only) | Scanned at runtime; no code changes unless default path config needed | Phase: loader |
| `README.md` | Run instructions for Pi 5 + Web UI | Phase: docs |

### Explicitly NOT modified

| Artifact | Reason |
|----------|--------|
| `src/hex_detector/` | Separate milestone; no merge |
| `src/block_detected*`, `src/view/`, `src/stream/` | Legacy; out of scope per PROJECT.md |
| `models/*.pt` weights | Do not edit model files |

### External system boundaries

```
┌──────────────┐     LAN HTTP/WS      ┌─────────────────────┐
│ Browser UI   │ ◀──────────────────▶ │ detect_only_v4 API  │
└──────────────┘                      └──────────┬──────────┘
                                               │
                    ┌──────────────────────────┼──────────────────────────┐
                    │                          │                          │
             ┌──────▼──────┐           ┌───────▼───────┐          ┌───────▼───────┐
             │ Picamera2 / │           │ Ultralytics   │          │ models/       │
             │ V4L2 / USB  │           │ YOLO runtime  │          │ (.pt/.onnx/   │
             │             │           │               │          │  NCNN dirs)   │
             └─────────────┘           └───────────────┘          └───────────────┘

Future robot/telemetry consumers ──▶ REST/WS JSON (DetectionResult) — no code coupling now
```

## Suggested Build Order

Order respects compile-time and runtime dependencies. Each step should be testable in isolation before the next.

| Step | Build | Depends On | Delivers | Test Gate |
|------|-------|------------|----------|-----------|
| **1** | `core/types` + `core/protocols` + `core/errors` | — | `DetectionResult`, ABCs, error types | Unit: serialize/deserialize JSON schema |
| **2** | `models/backends/pytorch` + `models/loader` + `models/inspector` | Step 1 | `load_model`, `inspect_model`, `.pt` discovery from `models/` | Unit: inspect known `.pt`; mock predict |
| **3** | `detectors/detect/adapter` + `registry` + `normalize_results` | Steps 1–2 | Detect task end-to-end on still image | Unit: fixture Results → DetectionResult |
| **4** | `cameras/opencv` + `discovery` + `probe_camera` | Step 1 | `discover_cameras`, `probe_camera` | Unit: mock VideoCapture; manual USB test |
| **5** | `pipeline/queue` + `worker` + `detect_frame` | Steps 2–4 | Single-threaded detect on live or file source | Integration: file/webcam loop, metrics |
| **6** | `render/overlay` + `drawers/detect` | Steps 1, 3 | Visual overlay for detect | Unit: blank frame + result → ndarray shape |
| **7** | `detectors/segment`, `pose`, `obb` + matching drawers | Steps 3, 6 | All four task adapters + overlays | Unit per task with sample outputs |
| **8** | `models/backends/ncnn` (+ onnx/tflite stubs) | Step 2 | Pi-optimized path; NCNN dir discovery | Pi hardware: NCNN inference benchmark |
| **9** | `cameras/v4l2` + `cameras/picamera2` | Step 4 | Native res/FPS on Pi | Pi: probe CSI + USB |
| **10** | `pipeline/session` + `capture` thread | Steps 5, 9 | Full threaded pipeline, drop-old-frame | Stress: queue drop metrics under load |
| **11** | `api/app` + REST routes | Steps 4, 2, 10 | List cameras/models, health, config | httpx TestClient |
| **12** | `api/websocket` + static UI | Step 11 | Live overlay + JSON stream | Manual LAN browser test |
| **13** | `config/store` + runtime switch model/camera | Steps 10–11 | Hot swap without full restart where safe | Integration: switch endpoints |
| **14** | `pyproject.toml` entry point + README | Step 12 | Shippable milestone artifact | `python -m detect_only_v4` on Pi |

**Parallelization opportunities:**

- Steps 4 (cameras) and 2–3 (model/detect adapter) can proceed in parallel after Step 1.
- Steps 7 (extra task adapters) can trail Step 6 — detect-only path unblocks pipeline + API MVP.
- Step 8 (NCNN backend) can start after Step 2; does not block desktop dev on `.pt`.

**MVP slice (minimum demo):** Steps 1 → 2 → 3 → 4 → 5 → 6 → 11 → 12 with **detect task only** and **OpenCV camera**. Pi-specific backends (8–9) and extra tasks (7) follow without restructuring.

## Scalability Considerations

| Concern | Dev desktop | Pi 5 production | Many LAN clients |
|---------|-------------|-----------------|------------------|
| Inference throughput | `.pt` acceptable | NCNN backend, smaller model | Same; one inference pipeline |
| Latency | Unbounded queue N/A | `maxsize=1` drop-old | Snapshot read is O(1) |
| Memory | Full-res frames | Match camera native or config downscale | JPEG bytes only over WS |
| Concurrency | Single user | `--workers 1` | Multiple WS clients read same snapshot |
| Config changes | In-memory | JSON persist optional | REST PATCH `/config` |

## Sources

- [PROJECT.md](../PROJECT.md) — milestone v2.0 requirements, greenfield scope, API surface
- [Ultralytics Predict mode](https://docs.ultralytics.com/modes/predict/) — `Results` attributes per task (HIGH)
- [Ultralytics tasks overview](https://docs.ultralytics.com/tasks/) — detect/segment/pose/OBB (HIGH)
- [Ultralytics NCNN export](https://docs.ultralytics.com/integrations/ncnn/) — Pi deployment format (HIGH)
- [Ultralytics Raspberry Pi guide](https://docs.ultralytics.com/guides/raspberry-pi/) — NCNN priority on ARM (HIGH)
- FastAPI WebSocket + threaded capture patterns — community producer-consumer (MEDIUM; aligns with official asyncio threading guidance)

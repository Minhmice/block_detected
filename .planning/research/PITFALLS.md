# Domain Pitfalls

**Domain:** Detect Only v4 — modular YOLO inference on Raspberry Pi 5 with Pi camera + FastAPI Web UI  
**Project:** Detect Only v4 (milestone v2.0)  
**Researched:** 2026-07-03  
**Overall confidence:** HIGH (stack/architecture), MEDIUM (phase numbering — roadmap not finalized)

---

## Critical Pitfalls

Mistakes that cause rewrites, silent wrong results, or “works on desktop, dead on Pi 5.”

### Pitfall 1: Treating all YOLO export formats as interchangeable loaders

**What goes wrong:** Code paths assume `YOLO(path)` works the same for `.pt`, `.onnx`, `.engine`, `.tflite`, and NCNN folders. On Pi 5, `.engine` (TensorRT) is not a viable target (no NVIDIA GPU/CUDA). TFLite export naming changed in Ultralytics ≥8.4.83 (`litert` replaces standalone `tflite` export flag while still producing `.tflite` files). NCNN exports a **directory** (`yolo26n_ncnn_model/`) with `.param`/`.bin`, not a single file. ONNX end-to-end vs grid layouts differ by YOLO generation and export flags.

**Why it happens:** Ultralytics `YOLO()` abstracts formats, so developers skip per-format discovery rules and postprocess differences.

**Consequences:** Model discovery lists `.engine` files that fail at runtime on Pi; NCNN folder not recognized; ONNX/OBB/seg/pose outputs parsed with detect-only logic; silent bbox corruption.

**Prevention:**
- Discovery whitelist by extension **and** structure (NCNN dir must contain expected artifacts).
- Platform gate: mark `.engine` as **unsupported on Pi** with explicit error, not lazy load failure.
- Route each format through `inspect_model()` before first `detect_frame()`.
- Unit-test one fixture per format (pt, onnx, ncnn dir, tflite) with golden output shapes.

**Detection:** Startup logs show “loaded model” but wrong task adapter or zero detections on known-good frame; `inspect_model` task ≠ adapter used.

**Address in phase:** Model discovery + multi-format loading (Phase 2)

---

### Pitfall 2: Guessing model family/task from filename or first inference

**What goes wrong:** Heuristics like `"seg" in filename → segment`, or “run predict and see what keys exist” pick the wrong adapter. Custom `best.pt` names carry no task signal. Exported ONNX/TFLite may lack embedded metadata if not produced by Ultralytics exporter.

**Why it happens:** Filename rules are easy to write; authoritative metadata requires format-specific readers.

**Consequences:** Pose keypoints parsed as boxes; OBB angles dropped; segment masks misaligned; robot telemetry gets wrong schema.

**Prevention (no guessing):**
| Format | Authoritative task source | Fallback (explicit failure) |
|--------|---------------------------|-----------------------------|
| `.pt` | `YOLO(path).task`, `model.names`, `model.yaml` | Refuse load if `task` missing |
| `.onnx` | Ultralytics embedded metadata / `metadata.yaml` sidecar | Probe ONNX output tensor shapes + documented layout table |
| NCNN folder | `metadata.yaml` in export dir (Ultralytics writes `task`, `imgsz`, `names`, `stride`) | Refuse if metadata missing |
| `.tflite` / LiteRT | TFLite metadata + `metadata.yaml` from export | Refuse INT8 without calibration notes in inspect |
| `.engine` | TensorRT + Ultralytics metadata (desktop only) | N/A on Pi |

- `inspect_model()` returns `{family, task, imgsz, names, stride, format, end2end}` — **never** infer task from filename alone.
- Log inspection result at load; expose in Web UI model card.

**Detection:** `DetectionResult` schema mismatches UI; mask tensor present but adapter is `DetectAdapter`.

**Address in phase:** Core API + `inspect_model` (Phase 1), reinforced in task adapters (Phase 3)

---

### Pitfall 3: Using OpenCV `VideoCapture(0)` as default on Pi 5

**What goes wrong:** `cv2.VideoCapture(0)` or V4L2 on Pi 5 with libcamera stack returns empty frames, striped frames, or pipeline errors. Legacy `start_x=1` camera stack does not exist on Pi 5.

**Why it happens:** Desktop tutorials and `src/stream/server.py` pattern (`VideoCapture(0, CAP_V4L2)`) copy-paste to Pi without backend abstraction.

**Consequences:** Black frames, 0 FPS, hours lost on “OpenCV bug”; Picamera2 never tried.

**Prevention:**
- **Pi CSI camera:** Picamera2 native (`capture_array`) as primary; optional GStreamer `libcamerasrc` only if Picamera2 unavailable.
- **USB webcam:** V4L2 via OpenCV with negotiated property readback.
- `probe_camera()` returns **actual** width/height/fps/format/backend — not requested values.
- `discover_cameras()` order: Picamera2 CSI → V4L2 devices → explicit failure message with remediation.

**Detection:** `cap.read()` succeeds but `frame.size == 0` or constant black; requested 1920×1080, actual 640×480.

**Address in phase:** Camera discovery + backends (Phase 4)

---

### Pitfall 4: Picamera2 resolution/FPS “set and forget”

**What goes wrong:** Requested resolution not in sensor mode table → driver picks nearest mode with different crop/FPS; `create_preview_configuration` vs `create_video_configuration` mismatch; RGB vs BGR confusion; no warmup after `start()`.

**Why it happens:** Picamera2 negotiates modes silently; legacy `block_detected_v1` uses fixed `create_preview_configuration` + `time.sleep(0.5)` without readback.

**Consequences:** Wrong aspect ratio breaks overlay alignment; inference `imgsz` mismatch; unstable first N frames; higher latency than necessary.

**Prevention:**
- Use `create_video_configuration` for sustained capture (not preview) when targeting inference FPS.
- After configure/start, log `camera.camera_configuration()` and first frame shape.
- Map `imgsz` from **actual** frame dimensions, not config intent.
- Warmup: discard first 5–10 frames after start.
- Document BGR conversion if model expects BGR (Picamera2 often RGB888).

**Detection:** Overlay boxes drift vs objects; `probe_camera` reports different dims than `detect_frame` sees.

**Address in phase:** Camera discovery + backends (Phase 4), overlay pipeline (Phase 3)

---

### Pitfall 5: Single-threaded capture + inference on Pi (or shared YOLO instance across threads)

**What goes wrong:** Camera read blocks during 200–800 ms inference (PyTorch on Pi); or multiple threads call `predict()` on one `YOLO` instance → race conditions and corrupt state (Ultralytics official guidance).

**Why it happens:** `block_detected_v1/runtime/frame_loop.py` runs read→infer→render synchronously; single `YoloDetector` shared without lock.

**Consequences:** Camera buffer backlog (seconds of lag); unpredictable detections; Web UI shows stale video; one inference exception kills entire loop (`return None`).

**Prevention:**
- **Producer thread/process:** capture only, push to bounded queue.
- **Consumer thread:** inference + normalize only.
- **Queue size 1–2, drop-oldest policy** (not unbounded `Queue(128)`).
- One model instance per inference worker; if shared, wrap with `ThreadingLocked()` (serializes — acceptable only for memory-bound cases).
- Recoverable inference errors: log + skip frame; fatal errors: structured shutdown.

**Detection:** FPS display high but video lags behind reality; queue depth grows; non-deterministic results under load.

**Address in phase:** Threaded runtime pipeline (Phase 5)

---

### Pitfall 6: FastAPI async handler doing JPEG encode + base64 on the event loop

**What goes wrong:** `async def` WebSocket loop calls `cv2.imencode`, overlay draw, and `base64.b64encode` inline → blocks asyncio event loop; HTTP config endpoints stall; multi-client streaming degrades.

**Why it happens:** Copying synchronous OpenCV view loop into `async def` without executor offload.

**Consequences:** 200–500 ms+ UI latency; config changes time out; “realtime” preview feels slideshow.

**Prevention:**
- Separate **capture/inference thread** from **web event loop**; pass already-encoded bytes or numpy via thread-safe latest-frame slot (atomic replace).
- Prefer **binary WebSocket frames** (raw JPEG bytes) over base64 JSON (~33% overhead + encode cost).
- Offload encode to thread pool if must run in web process; consider `PyTurboJPEG` over `cv2.imencode`.
- Single uvicorn worker unless Redis pub/sub for multi-worker broadcast.
- Throttle stream to display FPS (e.g., 10–15 Hz) decoupled from camera FPS.

**Detection:** `GET /config` slow while stream connected; CPU pegged in main thread; latency grows with clients.

**Address in phase:** FastAPI WebSocket UI (Phase 6)

---

### Pitfall 7: Assuming NCNN always wins on Pi 5 (or skipping validation)

**What goes wrong:** Hard-code NCNN-only path; skip accuracy/latency validation per model size. Third-party benchmarks disagree (Ultralytics official Pi 5 table: NCNN ~68 ms vs PyTorch ~302 ms for YOLO26n; some community posts show NCNN slower than ONNX/MNN in specific setups).

**Why it happens:** “NCNN priority” in PROJECT.md interpreted as “NCNN only,” not “prefer when available and validated.”

**Consequences:** Slower than OpenVINO/ONNX on a given model; export mismatch; missing Vulkan dependency on headless Pi.

**Prevention:**
- **Priority order (Pi 5):** NCNN dir → ONNX (OpenVINO runtime if integrated) → `.pt` for dev fallback.
- `inspect_model` + micro-benchmark on first load (optional, cached).
- `model.val()` or single-frame golden compare after NCNN export.
- Document NCNN export must be from same Ultralytics version as runtime.

**Detection:** NCNN slower than PyTorch in logs; mAP drop vs `.pt` on fixture image.

**Address in phase:** Pi optimization + format selection (Phase 7), discovery ranking (Phase 2)

---

## Technical Debt Patterns

Patterns that ship fast but ossify into rewrites if not caught early.

| Debt pattern | How it starts | Long-term cost | Early guard |
|--------------|---------------|----------------|-------------|
| **God loader** — one `load_model()` with 400 lines of if/elif per format | First milestone loads `.pt` only; formats bolted on | Untestable, fragile export upgrades | `ModelBackend` protocol per format; registry dict |
| **Leaky Ultralytics types** — `Results` objects escape core API | Quick adapter prototypes | Task adapters useless for NCNN-only deploy | `normalize_results()` is boundary; core uses `DetectionResult` only |
| **Config in Web UI only** — no single runtime config object | Web form fields added ad hoc | Hot-reload bugs, partial updates | Dataclass `RuntimeConfig` + atomic apply (lesson from `block_detected_v1` hot-reload) |
| **Implicit BGR/RGB** — conversion scattered | Picamera2 RGB passed to OpenCV draw | Color wrong, model preprocess wrong | Single `Frame` type with `color_space` enum |
| **Exception → stop everything** | Copy `frame_loop` `return None` on infer fail | One bad frame kills robot session | Error taxonomy: skip vs restart vs fatal |
| **Desktop-first tests** — no Pi CI, mocked camera only | Dev on Windows | Pi camera + NCNN break at integration | Markers: `@pytest.mark.pi`, fixture images per format |
| **Stream + inference same process, same thread** | MVP Web UI | Cannot hit FPS targets | Latest-frame slot pattern from day one |

---

## Integration Gotchas

Cross-component failures when YOLO + camera + Web UI meet.

### Camera frame ↔ model `imgsz`

- Letterbox/preprocess must use negotiated camera dimensions, not model default 640.
- Changing camera in Web UI must drain queue, reload warmup frames, and re-log actual resolution.

### Overlay ↔ JSON contract

- Draw overlay from **normalized** `DetectionResult`, not raw Ultralytics output — Web UI JSON and preview must share one source.
- OBB/pose/seg fields omitted vs `null` must be schema-stable for robot consumers.

### Web UI config ↔ inference thread

- Confidence/IOU/imgsz changes mid-stream require thread-safe config snapshot (copy-on-write or versioned atomic).
- Model hot-swap must unload old backend before loading new (memory spike on Pi if both loaded).

### Discovery ↔ runtime

- `models/` scan at startup vs watch folder — stale list if user drops new NCNN dir while running.
- NCNN folder name `*_ncnn_model` vs custom export dir naming — discovery by structure, not suffix alone.

### Picamera2 ↔ OpenCV overlay

- `cv2.rectangle` expects BGR; Picamera2 `RGB888` needs `cv2.cvtColor` once per frame (or configure `XBGR8888`).

### Ultralytics version ↔ export artifacts

- TFLite export flag migration (`litert`); metadata schema changes across 8.3→8.4+.
- Pin `ultralytics` in `pyproject.toml`; test export round-trip in README.

---

## Performance Traps

| Trap | Symptom | Fix |
|------|---------|-----|
| Unbounded frame queue | RAM climb, multi-second lag | `maxsize=1`, drop-oldest |
| Full-res inference (12 MP) | <1 FPS | Downscale for infer; overlay map coords back |
| PyTorch default on Pi | 300+ ms/frame | NCNN/ONNX path; `.pt` dev only |
| Base64 JSON WebSocket | High CPU, bandwidth | Binary JPEG WebSocket |
| `cv2.imencode` quality 95 | CPU burn | Quality 60–75 for preview; full quality on snapshot endpoint only |
| Multiple WebSocket clients | Linear CPU increase | Fan-out from single encoded buffer; throttle |
| GIL + pure-Python postprocess | Capture starved | Keep postprocess in C/numpy; or multiprocessing for infer |
| Logging every detection | I/O bound | Rate-limit DET logs (lesson from `frame_loop` primary log dedup) |
| No `CAP_PROP_BUFFERSIZE=1` on USB cam | Stale frames | Set buffer 1 on V4L2 where supported |

**Pi 5 realistic targets (Ultralytics benchmarks, YOLO26n, 640px, HIGH confidence):**

| Format | Inference ms/img | Notes |
|--------|------------------|-------|
| NCNN | ~68 | Recommended production path |
| OpenVINO | ~71 | Strong alternative |
| ONNX | ~130 | Acceptable fallback |
| PyTorch | ~302 | Dev/debug only |
| TFLite | ~251 | Usually not first choice on Pi 5 |

---

## "Looks Done But Isn't" Checklist

Shippable-looking behavior that fails UAT or production on Pi.

- [ ] **Model loads** — but task adapter wrong; JSON missing masks/keypoints/OBB angles
- [ ] **Camera opens** — but frames are black/empty on Pi 5 CSI (OpenCV path)
- [ ] **Live preview works** — but 2–5 s behind real world (unbounded queue)
- [ ] **Web UI shows boxes** — but coordinates wrong after resolution change (no re-probe)
- [ ] **NCNN "enabled"** — but still loading `.pt` because discovery sort order wrong
- [ ] **WebSocket streams** — but HTTP config dead during stream (event loop blocked)
- [ ] **Tests pass on CI** — but no test for NCNN folder layout or `metadata.yaml` parse
- [ ] **inspect_model exists** — but falls back to filename guess on unknown format
- [ ] **Error handling** — but one inference exception stops camera (legacy `frame_loop` pattern)
- [ ] **FPS counter** — shows high FPS while display lags (measuring capture, not end-to-end latency)
- [ ] **Multi-format support** — `.engine` listed on Pi then fails with cryptic TensorRT error
- [ ] **README quickstart** — works on laptop webcam, never validated on Pi 5 + Picamera2

---

## Moderate Pitfalls

### Pitfall: TensorRT `.engine` in model discovery on Pi

**What goes wrong:** User copies desktop `.engine` to `models/`; load fails or worse, wrong arch.

**Prevention:** Platform capability matrix in `discover_models()`; filter or tag as `requires_cuda`.

**Address in phase:** Model discovery (Phase 2)

---

### Pitfall: INT8 TFLite without calibration metadata

**What goes wrong:** Quantized model drifts; confidence calibration wrong.

**Prevention:** `inspect_model` reports quantization type; warn if INT8 and no `data` provenance.

**Address in phase:** Model inspection (Phase 1)

---

### Pitfall: ONNX opset / end2end layout mismatch

**What goes wrong:** YOLO11 grid ONNX vs YOLO26 end2end `(N, 300, 6)` parsed with wrong decoder.

**Prevention:** `inspect_model.end2end` flag drives postprocess; test fixtures per family.

**Address in phase:** Task adapters (Phase 3)

---

### Pitfall: Picamera2 resource leak on camera switch

**What goes wrong:** `stop()`/`close()` skipped on switch → “Camera in use” until reboot.

**Prevention:** Context manager for camera session; switch = full teardown + warmup.

**Address in phase:** Camera backends (Phase 4)

---

### Pitfall: WebSocket no heartbeat / disconnect cleanup

**What goes wrong:** Dead clients hold references; background tasks leak (common FastAPI WebSocket bug).

**Prevention:** Cancel stream task on disconnect; weak ref to latest frame buffer.

**Address in phase:** Web UI (Phase 6)

---

## Minor Pitfalls

### Pitfall: Assuming USB and CSI can share one code path

**Prevention:** `CameraBackend` enum; separate probe logic.

### Pitfall: `multiprocessing` + CUDA/model on Pi

**Prevention:** Prefer threading + NCNN on Pi; multiprocessing adds pickling overhead, often unnecessary.

### Pitfall: Huge `models/` scan every HTTP request

**Prevention:** Cache discovery with mtime-based invalidation.

---

## Pitfall-to-Phase Mapping

Suggested v2.0 phase ordering for roadmap consumer. Phases align with PROJECT.md feature groups.

| Phase | Focus | Pitfalls to address in success criteria | Quality gate |
|-------|-------|----------------------------------------|--------------|
| **1 — Core API & contracts** | `load_model`, `inspect_model`, `DetectionResult`, logging | #2 guessing task; INT8 metadata; exception taxonomy | `inspect_model` returns authoritative task for `.pt` + fails loudly without metadata on exports |
| **2 — Model discovery & formats** | Scan `models/`, NCNN dir, platform gates | #1 interchangeable loaders; `.engine` on Pi; ONNX layout; debt: god loader | One test per format; Pi marks `.engine` unsupported |
| **3 — Task adapters & overlay** | detect/segment/pose/obb normalize + draw | #2 wrong adapter; ONNX end2end; overlay/JSON single source | Golden-frame tests per task; no filename heuristics |
| **4 — Camera discovery & backends** | Picamera2, V4L2, `probe_camera` | #3 OpenCV on Pi 5; #4 resolution negotiation; BGR/RGB; leak on switch | Pi 5 CSI test: non-zero frames, actual dims logged |
| **5 — Threaded runtime pipeline** | Bounded queue, drop-old, infer thread | #5 threading/GIL; unbounded queue; infer exception stops camera | Queue maxsize=1; lag < 500 ms on fixture stream; skip-frame on error |
| **6 — FastAPI WebSocket UI** | List cameras/models, stream, config | #6 event loop blocking; base64 overhead; disconnect leak; config race | HTTP responsive during stream; binary JPEG path; p95 latency budget documented |
| **7 — Pi optimization & hardening** | NCNN priority, README, benchmarks | #7 NCNN assumptions; performance traps table | Benchmark table in README; NCNN vs ONNX logged on load |

### Phase ordering rationale

1. **Inspect before discover** — metadata contract prevents discovery from encoding guesses.
2. **Adapters before camera** — validate inference on still images before realtime threading.
3. **Camera before threading** — probe actual frames before queue architecture.
4. **Threading before Web UI** — UI attaches to latest-frame slot, not inline infer.
5. **Optimization last** — format ranking needs working pipeline to benchmark.

### Research flags for phases

| Phase | Deeper research likely? | Topic |
|-------|---------------------------|-------|
| 2 | YES | OpenVINO on Pi 5 vs NCNN for project’s specific model sizes |
| 3 | MAYBE | OBB/pose tensor layouts per export format |
| 4 | YES | Picamera2 sensor mode tables for Camera Module 3 |
| 6 | MAYBE | WebRTC vs WebSocket JPEG for LAN latency targets |
| 7 | YES | Vulkan NCNN on headless Pi 5 |

---

## Sources

| Source | Confidence | Used for |
|--------|------------|----------|
| [Ultralytics Raspberry Pi guide](https://docs.ultralytics.com/guides/raspberry-pi/) | HIGH | NCNN vs PyTorch benchmarks, format recommendations |
| [Ultralytics NCNN integration](https://docs.ultralytics.com/integrations/ncnn/) | HIGH | NCNN folder export, metadata, validation |
| [Ultralytics model export](https://docs.ultralytics.com/modes/export/) | HIGH | Format table, metadata, end2end layouts |
| [Ultralytics TFLite/LiteRT](https://docs.ultralytics.com/integrations/tflite/) | HIGH | TFLite→LiteRT migration |
| [Ultralytics thread-safe inference](https://docs.ultralytics.com/guides/yolo-thread-safe-inference/) | HIGH | Shared model race conditions |
| [Ultralytics multi-stream / drop frames](https://academy.ultralytics.com/courses/yolo-in-production/multi-stream-inference) | HIGH | Queue drop policy |
| [Picamera2 OpenCV issue #617](https://github.com/raspberrypi/picamera2/issues/617) | HIGH | OpenCV lacks libcamera; use Picamera2 |
| [OpenCV Pi 5 issue #25072](https://github.com/opencv/opencv/issues/25072) | HIGH | V4L2 empty frames on Pi 5 |
| [FastAPI WebSocket scaling guide](https://websocket.org/guides/frameworks/fastapi/) | MEDIUM | Event loop blocking, worker model |
| [GitHub ultralytics#19210](https://github.com/ultralytics/ultralytics/issues/19210) | MEDIUM | Queue(1) drop-old pattern |
| `src/block_detected_v1/runtime/frame_loop.py` | HIGH | Sync pipeline, fatal infer error |
| `src/block_detected_v1/io/camera/pi/picamera2.py` | HIGH | Preview config, no readback |
| `src/stream/server.py` | HIGH | V4L2 `VideoCapture(0)` anti-pattern on Pi 5 |
| `.planning/PROJECT.md` | HIGH | v2.0 scope, NCNN priority, greenfield module |
| `.planning/codebase/CONCERNS.md` | MEDIUM | Legacy hot-reload, infer failure handling |

---

*Pitfalls research for milestone v2.0 — feeds roadmap phase success criteria and ordering.*

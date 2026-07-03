# Technology Stack — Detect Only v4 (Milestone v2.0)

**Project:** Detect Only v4 — modular YOLO inference on Raspberry Pi 5  
**Module:** `src/detect_only_v4/` (greenfield; no legacy imports)  
**Researched:** 2026-07-03  
**Overall confidence:** HIGH (Ultralytics Pi 5 guide + official export docs + Pi camera ecosystem issues verified)

---

## Recommended Stack

### Core Technologies

| Technology | Version (Pi 5 / dev) | Purpose | Why |
|------------|----------------------|---------|-----|
| **Python** | **3.11** on Pi (Bookworm default); **3.11–3.12** dev/CI | Runtime | Ultralytics officially supports up to 3.12; Pi Bookworm ships 3.11.2. Avoid 3.13 on Pi — reported NCNN/torch wheel conflicts. |
| **ultralytics** | **≥8.4.14, &lt;9.0** | YOLO load, inspect, predict, export discovery | Pi 5 YOLO26/NCNN benchmarks published at 8.4.14; single API for `.pt`, `.onnx`, `*_ncnn_model/`, `*_openvino_model/`, `.tflite`. Task adapters wrap `Results` objects. |
| **torch** | **≥2.5** (resolve via pip on aarch64) | `.pt` inference + export toolchain | Required by ultralytics; let pip resolve aarch64 wheels — do not pin old torch unless `illegal instruction` occurs. |
| **torchvision** | **matched to torch** | torchvision ops for ultralytics | Must match torch wheel from same index; manual pins are a last resort on Pi. |
| **ncnn** | **≥1.0.20260114** (via `ultralytics[export]`) | NCNN backend for `*_ncnn_model/` folders | Fastest format on Pi 5 (~68 ms/im YOLO26n vs ~302 ms PyTorch). Pulled automatically with export extra. |
| **onnx** | **≥1.12.0** | ONNX graph for `.onnx` files | Ultralytics export/runtime dependency. |
| **onnxruntime** | **≥1.22.0** (Pi); latest **1.27.x** OK on x86 dev | `.onnx` fallback runtime | aarch64 wheels available; 1.21.0 had `illegal instruction` on some Pi 4/5 builds — use ≥1.22. XNNPACK provider included in CPU wheel. |
| **openvino** | **≥2024.3** (via `ultralytics[export]`) | `*_openvino_model/` folders | Second-fastest on Pi 5 (~71 ms/im YOLO26n). Official NCNN crash fallback per Ultralytics community guidance. |
| **opencv** | **apt: 4.6+** (`python3-opencv`) on Pi; **pip: opencv-python-headless ≥4.8** dev | V4L2/USB capture, overlay draw, resize | On Pi, **apt OpenCV** avoids numpy/simplejpeg binary clash with Picamera2. Headless pip build for Windows/Linux dev without GUI. |
| **picamera2** | **apt: ≥0.3.19** (`python3-picamera2`) | CSI camera on Pi 5 | Native libcamera stack; pre-installed on Pi OS Bookworm. **Do not pip-install** on Pi — use system package in `--system-site-packages` venv. |
| **numpy** | **1.24.x** (Pi with system packages); **≥1.23, &lt;2.3.6** (pip-only dev) | Frame buffers, ultralytics arrays | Picamera2/simplejpeg on Bookworm built against numpy 1.x. Pip `opencv-python` pulls numpy 2.x and breaks Picamera2 unless entire stack is pip-only with simplejpeg ≥1.7.4. |
| **fastapi** | **≥0.115, &lt;0.140** | REST + WebSocket UI | Mature async WebSocket (`send_bytes`, `send_json`); pairs with uvicorn. Use `fastapi[standard]` for recommended extras. |
| **uvicorn** | **≥0.30, &lt;0.50** | ASGI server | `[standard]` extra pulls `uvloop`, `httptools`, `websockets` — better LAN preview throughput. |
| **pydantic** | **≥2.0** (via fastapi) | Request/response + runtime config schemas | FastAPI v2 native; use for `DetectionResult` API contracts and WebSocket message envelopes. |

### Inference Backend Priority (Pi 5 runtime)

When multiple formats exist for the same model stem, `detect_only_v4` should select backends in this order:

| Priority | Discovery pattern | Loader | Pi 5 inference (YOLO26n, 640px) |
|----------|-------------------|--------|----------------------------------|
| 1 | `{name}_ncnn_model/` directory | `YOLO("{name}_ncnn_model")` | ~68 ms/im — **default on Pi** |
| 2 | `{name}_openvino_model/` directory | `YOLO("{name}_openvino_model")` | ~71 ms/im — fallback if NCNN unstable |
| 3 | `{name}.onnx` | `YOLO("{name}.onnx")` | ~130 ms/im — portable dev fallback |
| 4 | `{name}.tflite` | `YOLO("{name}.tflite")` | ~251 ms/im — discover + load; low priority |
| 5 | `{name}.pt` | `YOLO("{name}.pt")` | ~302 ms/im — always works; use for inspect/export only on Pi |
| — | `{name}.engine` | Discover only → **unsupported on Pi** | TensorRT requires NVIDIA GPU; surface clear error, do not attempt load |

**NCNN folder contract:** Ultralytics export produces a directory (e.g. `yolo26n_ncnn_model/`) containing `model.ncnn.param`, `model.ncnn.bin`, and metadata — not a single file. Model discovery must treat trailing `_ncnn_model` directories as first-class artifacts.

**Task coverage:** YOLOv8/11/26 families expose `model.task` ∈ `{detect, segment, pose, obb, classify}`. Task adapters normalize ultralytics `Results` into `DetectionResult` regardless of backend.

### Camera Stack

| Source | Stack | Notes |
|--------|-------|-------|
| **Pi CSI (Camera Module 3)** | `picamera2.Picamera2` → numpy RGB → BGR for OpenCV overlay | Use `RGB888` format; Pi 5 needs 15-pin CSI cable. Configure native resolution/FPS via `preview_configuration` or `create_video_configuration`. |
| **USB / V4L2** | `cv2.VideoCapture(index)` or `cv2.VideoCapture("/dev/video0")` | Works on Pi and dev machines. Probe with `cap.get(cv2.CAP_PROP_FRAME_WIDTH)` etc. for native modes. |
| **rpicam TCP (optional)** | `rpicam-vid --listen -o tcp://127.0.0.1:8888` + `YOLO("tcp://...")` | Alternative when Picamera2 unavailable; higher latency. Defer to Phase 2+ unless needed. |

**Camera discovery API:** Enumerate V4L2 via `/dev/video*` + OpenCV probe; detect CSI via `libcamera-hello --list-cameras` or Picamera2 `Picamera2.global_camera_info()`.

### Pipeline Concurrency (bounded queue + inference thread)

| Component | Technology | Why |
|-----------|------------|-----|
| Frame buffer | `queue.Queue(maxsize=1)` or `maxsize=2` | Bounded queue; on full, **drop oldest** (not newest) to minimize latency. |
| Capture | Dedicated `threading.Thread` | Picamera2 `capture_array()` and `cv2.read()` block; must not stall FastAPI event loop. |
| Inference | Dedicated `threading.Thread` | NCNN/OpenVINO release GIL during native inference; keeps preview responsive. |
| Preview broadcast | `asyncio` + `WebSocket.send_bytes` | FastAPI async endpoints; bridge from inference thread via `asyncio.run_coroutine_threadsafe` or `janus.Queue` (async/sync bridge). |
| Shutdown | `threading.Event` + sentinel `None` in queue | Clean thread join on stop. |

**Do not** run inference inside FastAPI route handlers directly — a single YOLO26n NCNN frame (~70 ms) would block all WebSocket clients.

### Web UI / Live Preview

| Technology | Version | Purpose | Why |
|------------|---------|---------|-----|
| **WebSocket binary JPEG** | FastAPI built-in | Live overlay stream | `send_bytes` with JPEG payload (~30–70% less bandwidth than base64 JSON). Target 10–15 FPS preview, not full camera FPS. |
| **WebSocket JSON** | FastAPI built-in | Detection telemetry | Separate channel or interleaved metadata message with `DetectionResult` JSON per frame. |
| **REST** | FastAPI routes | List cameras/models, runtime config CRUD | Simple `GET /api/cameras`, `GET /api/models`, `POST /api/config`. |
| **Static UI** | `starlette.staticfiles` + vanilla JS or htmx | Control panel | No React build step on Pi; keep JS minimal. `fastapi[standard]` includes static file support patterns. |
| **JPEG encode** | `cv2.imencode('.jpg', frame, [IMWRITE_JPEG_QUALITY, 70])` | Frame compression for WS | Built-in; sufficient for MVP. Optional: `PyTurboJPEG` on Pi if CPU encode becomes bottleneck (LOW priority). |

---

## Supporting Libraries

| Library | Version | Purpose | When |
|---------|---------|---------|------|
| **pillow** | ≥7.1.2 | Image helpers, overlay fallbacks | ultralytics dependency; already pulled |
| **pyyaml** | ≥5.3.1 | Model metadata, config files | ultralytics + local YAML configs |
| **httpx** | ≥0.27 | Async test client | `pytest` + FastAPI `TestClient` / `httpx.AsyncClient` |
| **pytest** | ≥8.0 | Unit tests | Model discovery, queue drop policy, adapter normalization |
| **python-multipart** | ≥0.0.6 | Form uploads (optional) | If UI supports image upload for single-frame detect |
| **aiofiles** | ≥23.0 | Async static file reads | Optional; only if serving large assets |
| **psutil** | ≥5.8.0 | Pi resource metrics in UI | Optional telemetry (CPU%, thermals) |
| **pnnx** | via `ultralytics[export]` | NCNN export toolchain | Export-time only; not needed at Pi runtime if models pre-exported |
| **tensorflow** / **ai-edge-litert** | via export extra | `.tflite` export/load | Only if TFLite discovery required; heavy — lazy-import |

---

## Pi 5 Specific Considerations

### OS and Python environment

```bash
# Target: Raspberry Pi OS Bookworm 64-bit (aarch64)
# Python 3.11.2 system interpreter

sudo apt update
sudo apt install -y \
  python3-pip python3-venv \
  python3-picamera2 python3-opencv python3-numpy \
  libcamera-apps  # rpicam-hello, rpicam-vid

python3 -m venv --system-site-packages .venv
source .venv/bin/activate
pip install -U pip
pip install "ultralytics[export]>=8.4.14" "fastapi[standard]>=0.115" "uvicorn[standard]>=0.30"
```

**Why `--system-site-packages`:** Shares apt-installed `picamera2`, `cv2`, and numpy 1.24 without binary incompatibility. Pip installs only ultralytics stack + FastAPI on top.

### Power and thermal

- Pi 5 draws up to **5A @ 5V** under sustained NCNN load — inadequate PSU causes freezes misreported as NCNN bugs.
- Prefer **Pi OS Lite** (no desktop) for headless robot deployments; frees ~200 MB RAM.
- Optional SSD via PCIe HAT for 24/7 logging; SD card wear is a deployment concern, not a stack choice.

### Model format guidance for Pi deployment

Pre-export on dev machine or Pi once, ship artifacts to `models/`:

```bash
yolo export model=yolo26n.pt format=ncnn      # → yolo26n_ncnn_model/
yolo export model=yolo26n.pt format=openvino  # → yolo26n_openvino_model/ (fallback)
yolo export model=yolo26n.pt format=onnx      # → yolo26n.onnx (portable)
```

Avoid running `.pt` inference in production on Pi — 4–5× slower than NCNN with full torch RAM footprint.

### OpenCV + Picamera2 pixel format

- Picamera2 `RGB888` → convert to BGR for `cv2` drawing: `cv2.cvtColor(frame, cv2.COLOR_RGB2BGR)`.
- Ultralytics accepts numpy HWC uint8 arrays directly.

### Docker alternative (validated)

```bash
t=ultralytics/ultralytics:latest-arm64
sudo docker pull $t && sudo docker run -it --ipc=host $t
```

Useful for reproducible export; for integrated FastAPI + Picamera2 app, **native venv is simpler** (camera device passthrough in Docker adds complexity). Confidence: MEDIUM for Docker+Picamera2 combined deployment.

---

## What NOT to Use

| Avoid | Why | Use instead |
|-------|-----|-------------|
| **CUDA / TensorRT on Pi** | Pi 5 has VideoCore GPU, not CUDA; `.engine` export requires NVIDIA GPU | NCNN → OpenVINO → ONNX priority chain |
| **`pip install opencv-python` on Pi with Picamera2** | Upgrades numpy to 2.x; breaks `simplejpeg`/Picamera2 with `ValueError: numpy.dtype size changed` | `apt install python3-opencv` + `--system-site-packages` venv |
| **`pip install picamera2` on Pi** | Duplicates/conflicts with system libcamera stack | `apt install python3-picamera2` |
| **Python 3.13 on Pi production** | Ultralytics reports dependency issues; NCNN export failures reported | Python 3.11 (Bookworm) or 3.12 |
| **Base64 WebSocket video** | ~33% bandwidth overhead vs binary JPEG | `websocket.send_bytes(jpeg_bytes)` |
| **aiortc / FFmpeg H.264 pipeline** | High complexity for MVP; WebCodecs needs HTTPS | JPEG binary WebSocket for v2.0 |
| **asyncio-only inference (no thread)** | Blocks event loop; starves WebSocket pings | Dedicated inference `threading.Thread` |
| **unbounded `queue.Queue`** | Memory growth under load; stale frames increase latency | `maxsize=1`, drop-old policy |
| **Legacy `block_detected*` imports** | Milestone constraint — greenfield module | Self-contained `detect_only_v4` packages |
| **Object tracking (ByteTrack, etc.)** | Explicitly out of scope per PROJECT.md | Raw per-frame detections only |
| **GPIO / robotic actuation in core** | Out of scope for inference platform | JSON telemetry output for downstream consumers |

---

## Version Compatibility Matrix

| Combination | Status | Notes |
|-------------|--------|-------|
| ultralytics 8.4.14 + Pi 5 + NCNN | ✅ Verified | Official benchmark source |
| ultralytics 8.4.14 + Python 3.11 + Bookworm | ✅ Recommended | Default Pi OS |
| ultralytics 8.4.x + Python 3.13 | ⚠️ Avoid on Pi | Community reports install/runtime issues |
| Picamera2 (apt) + numpy 1.24 + python3-opencv (apt) | ✅ Recommended Pi stack | System package alignment |
| Picamera2 (apt) + pip opencv-python + numpy 2.x | ❌ Broken | Binary incompatibility |
| onnxruntime 1.21.0 + Pi 4/5 aarch64 | ⚠️ Risk | `illegal instruction` — use ≥1.22 |
| onnxruntime ≥1.22 + Pi 5 | ✅ Expected | XNNPACK provider |
| torch 2.6+ + ultralytics NCNN export | ✅ Fixed in 8.4.14+ | Earlier 8.3.71 + torch 2.6 had export failures |
| NCNN runtime + marginal PSU | ⚠️ Risk | System freeze — hardware issue, not software |
| fastapi 0.115+ + uvicorn 0.30+ | ✅ Standard | WebSocket stable |
| `.engine` on Pi 5 | ❌ Unsupported | Discovery + error message only |
| Windows dev + opencv-python-headless + ultralytics | ✅ Dev/CI | No Picamera2; USB webcam via OpenCV |

### Suggested `pyproject.toml` optional extra (for roadmap)

```toml
[project.optional-dependencies]
detect-only = [
    "ultralytics>=8.4.14,<9.0",
    "opencv-python-headless>=4.8.0",
    "fastapi[standard]>=0.115,<0.140",
    "uvicorn[standard]>=0.30,<0.50",
    "onnxruntime>=1.22.0",
    "httpx>=0.27",
]
# Pi install notes (not pip): python3-picamera2, python3-opencv via apt
dev-detect-only = ["pytest>=8.0", "httpx>=0.27"]
```

Keep Pi system packages documented in README, not as pip deps — apt packages have no PEP 508 equivalent.

---

## Integration with `detect_only_v4` Module

```
models/                          # repo root model artifacts
src/detect_only_v4/
├── backends/                    # ultralytics YOLO wrapper per format
│   ├── priority.py              # NCNN > OpenVINO > ONNX > TFLite > PT
│   └── loader.py                # YOLO(path) + task inspection
├── cameras/
│   ├── v4l2.py                  # cv2.VideoCapture
│   └── picamera2.py             # Picamera2 (optional import; graceful on non-Pi)
├── pipeline/
│   ├── queue.py                 # bounded drop-old queue
│   ├── capture_thread.py
│   └── inference_thread.py
├── adapters/                    # task → DetectionResult
├── api/
│   ├── app.py                   # FastAPI factory
│   ├── routes.py                # REST
│   └── ws.py                    # WebSocket preview + JSON
└── core/
    ├── types.py                 # DetectionResult dataclasses
    └── discovery.py             # scan models/ + cameras
```

**Key principle:** ultralytics `YOLO` is the **only** inference engine — no parallel onnxruntime/ncnn Python bindings. Format-specific code is limited to discovery heuristics and backend priority selection; all `predict()` calls go through `YOLO(model_path)`.

---

## Alternatives Considered

| Category | Recommended | Alternative | Why not |
|----------|-------------|-------------|---------|
| Pi inference | NCNN via ultralytics | Raw `ncnn-python` bindings | Ultralytics already wraps NCNN; duplicate binding layer |
| Pi inference | NCNN | OpenVINO only | NCNN ~3% faster in official benchmarks; keep OpenVINO as fallback |
| Pi inference | NCNN | ONNX Runtime direct | ORT slower on Pi (~130 ms vs ~68 ms); ultralytics ONNX path sufficient as tertiary |
| Web preview | WebSocket JPEG | MJPEG `StreamingResponse` | WS allows bidirectional config; MJPEG OK as optional secondary endpoint |
| Web framework | FastAPI | Flask + SocketIO | FastAPI native async WS; better typing with Pydantic v2 |
| Camera (Pi) | Picamera2 | rpicam-vid TCP only | Picamera2 lower latency, direct numpy frames |
| Queue | `queue.Queue` | `asyncio.Queue` only | Threads need sync queue; bridge to async for WS |

---

## Installation

### Development (Windows / Linux x86)

```bash
pip install -e ".[detect-only,dev-detect-only]"
# or minimal:
pip install "ultralytics[export]>=8.4.14" "opencv-python-headless>=4.8" \
            "fastapi[standard]>=0.115" "uvicorn[standard]>=0.30" "onnxruntime>=1.22"
```

### Raspberry Pi 5 production

```bash
sudo apt install -y python3-picamera2 python3-opencv python3-venv
python3 -m venv --system-site-packages .venv && source .venv/bin/activate
pip install -U pip
pip install "ultralytics[export]>=8.4.14" "fastapi[standard]>=0.115" "uvicorn[standard]>=0.30"
# Pre-exported NCNN models in models/ — no export toolchain needed at runtime
```

---

## Sources

| Source | Confidence | Used for |
|--------|------------|----------|
| [Ultralytics Raspberry Pi guide](https://docs.ultralytics.com/guides/raspberry-pi/) | HIGH | NCNN priority, Pi 5 benchmarks, Picamera2 example, `ultralytics[export]` install |
| [Ultralytics export modes](https://docs.ultralytics.com/modes/export/) | HIGH | Format list, `.engine` GPU requirement |
| [Ultralytics NCNN integration](https://docs.ultralytics.com/integrations/ncnn/) | HIGH | NCNN folder layout, `*_ncnn_model` convention |
| [Ultralytics OpenVINO integration](https://docs.ultralytics.com/integrations/openvino/) | HIGH | `*_openvino_model/` load pattern |
| [Ultralytics TensorRT exporter source](https://docs.ultralytics.com/reference/engine/exporter/) | HIGH | `device!=cpu` assertion for `.engine` |
| [PyPI ultralytics 8.4.86](https://pypi.org/project/ultralytics/) | HIGH | Current version, dependency constraints |
| [PyPI fastapi 0.139 / uvicorn 0.49](https://pypi.org/project/fastapi/) | HIGH | Current web stack versions |
| [ONNX Runtime install docs](https://onnxruntime.ai/docs/install/) | HIGH | aarch64 wheel availability |
| [onnxruntime#23957 illegal instruction](https://github.com/microsoft/onnxruntime/issues/23957) | MEDIUM | Pi aarch64 1.21.0 bug, fixed 1.22+ |
| [picamera2#1088 numpy 2.x](https://github.com/raspberrypi/picamera2/issues/1088) | HIGH | numpy 1.x requirement on Bookworm |
| [Raspberry Pi Forums: opencv + picamera2](https://forums.raspberrypi.com/viewtopic.php?t=390353) | MEDIUM | apt opencv fix |
| [Ultralytics community: Pi 5 NCNN crash](https://community.ultralytics.com/t/raspberry-pi-5-crash-when-running-yolov11n-ncnn/1525) | MEDIUM | PSU/Python version troubleshooting |
| [Context7 /ultralytics/ultralytics](https://github.com/ultralytics/ultralytics) | HIGH | Export API patterns |
| [Context7 /fastapi/fastapi](https://github.com/fastapi/fastapi) | HIGH | WebSocket API, `fastapi[standard]` install |

---

## Open Questions (phase-specific research)

| Topic | Flag | Notes |
|-------|------|-------|
| Picamera2 + pip-only venv (no system-site-packages) | Phase: camera | Possible with numpy 2.x + simplejpeg 1.8.1 pip, but fragile on Bookworm — validate on hardware |
| TFLite vs LiteRT naming in ultralytics 8.4 | Phase: model discovery | Export may emit `format=tflite` or `litert` — discovery should accept both extensions |
| PyTurboJPEG on aarch64 | Phase: Web UI | Marginal gain; benchmark before adding dep |
| `janus` library for async/sync queue bridge | Phase: pipeline | stdlib-only preferred for MVP; evaluate if `run_coroutine_threadsafe` is insufficient |

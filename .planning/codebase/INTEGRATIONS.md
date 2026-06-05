# External Integrations

**Analysis Date:** 2026-06-05

## APIs & External Services

**HTTP/REST APIs:**
- None in application code — no `requests`, `httpx`, `aiohttp`, or similar imports under `src/` or `tests/`

**Ultralytics ecosystem (local-only usage):**
- YOLO inference via local weight files only
  - Discovery: `src/block_detected/detection/yolo/loader.py` → `discover_model_paths()` globs `models/*.pt`
  - Load: `YOLO(str(model_path))` in `src/block_detected/detection/yolo/backend.py`
  - No code paths call Ultralytics Hub download APIs or remote model URLs
  - Ultralytics may still perform internal network activity for optional features (updates, telemetry) when installed — not configured or invoked by this project

**Future UI reference (not integrated):**
- `example_ui/stitch_block_pickup_vision_console/code.html` describes a web-style console that would consume frame streams (base64 or MJPEG URL per `html_data_requirements.md`) — not connected to Python backend today

## Data Storage

**Databases:**
- None — no SQLAlchemy, sqlite3 usage for persistence, Redis, or ORM detected

**File Storage:**
- **Local filesystem only**
  - Model weights: `models/*.pt` (`src/block_detected/config/paths.py` → `MODELS_DIR`; binaries gitignored)
  - User config: `block_detected.toml` at repo root (`src/block_detected/runtime/config_store.py`)
  - Save from GUI: `save_config()` writes TOML via custom serializer in `config_store.py`
  - Training/inference output dirs `runs/`, `wandb/` — gitignored; not written by current GUI runtime

**Caching:**
- In-memory only:
  - Log ring buffer: `src/block_detected/runtime/logging_setup.py` → `LogBufferHandler` (capacity 500)
  - FPS rolling window: `src/block_detected/runtime/metrics.py` → `deque(maxlen=30)`
  - Temporal stability votes: `src/block_detected/runtime/postprocess.py` → `deque` per detection track

## Authentication & Identity

**Auth Provider:**
- Not applicable — single-user local desktop app with no login, tokens, or user accounts

## Hardware & OS Integrations

**Webcam (primary external integration):**
- OpenCV `cv2.VideoCapture` — `src/block_detected/io/camera/capture.py`
  - Opens camera by integer index (`camera.index`, default 0)
  - Sets resolution via `CAP_PROP_FRAME_WIDTH` / `CAP_PROP_FRAME_HEIGHT`
  - Camera cycling: `switch_camera()` tries indices up to `camera.max_index`
- Platform dependency: OS camera drivers (DirectShow/Media Foundation on Windows, V4L2 on Linux, AVFoundation on macOS)

**GPU (optional):**
- PyTorch/CUDA via Ultralytics — not explicitly configured in project code; follows Ultralytics/torch defaults when GPU available

**Desktop windowing:**
- PySide6/Qt6 — `src/block_detected/apps/gui/app.py`
  - `QThread` worker for frame loop
  - `QImage` from OpenCV BGR frames (`_frame_to_qimage`)
  - Headless test platform: `QT_QPA_PLATFORM=offscreen` in `tests/test_gui_smoke.py`

**Legacy OpenCV windows:**
- `src/block_detected/runtime/engine.py` → `shutdown(destroy_cv_windows=True)` can call `cv2.destroyAllWindows()`
- GUI worker passes `destroy_cv_windows=False` to avoid conflicting with Qt

## Monitoring & Observability

**Error Tracking:**
- None — no Sentry, Rollbar, or similar

**Logs:**
- Python stdlib `logging` — `src/block_detected/runtime/logging_setup.py`
  - StreamHandler → stdout with format `%(asctime)s [%(levelname)s] %(name)s: %(message)s`
  - Ring buffer handler for GUI log panel via `get_log_lines()`
  - Ultralytics logger level capped to WARNING
- No log file rotation or external log shipping

**Metrics:**
- In-process only — `src/block_detected/runtime/metrics.py` computes FPS and stage latencies (read/infer/render ms); displayed in GUI status bar via `RuntimeStatus`

## CI/CD & Deployment

**Hosting:**
- Not applicable — local desktop application, no server deployment target

**CI Pipeline:**
- Not detected — no `.github/workflows/`, GitLab CI, or similar in repo

**Containerization:**
- Not detected — no `Dockerfile` or `docker-compose`

## Environment Configuration

**Required env vars:**
- None for normal operation

**Optional env vars (testing only):**
- `QT_QPA_PLATFORM=offscreen` — headless PySide6 smoke test (`tests/test_gui_smoke.py`)

**Secrets location:**
- Not applicable — no API keys, credentials files, or secret directories in use
- `.env` / `.env.*` listed in `.gitignore` but no `.env` file present in repo

## Webhooks & Callbacks

**Incoming:**
- None — no HTTP server, WebSocket listener, or IPC service

**Outgoing:**
- None — no outbound HTTP calls, webhooks, or message queues from application code

## Third-party library boundaries

| Integration | Contact point | Direction | Notes |
|-------------|---------------|-----------|-------|
| OpenCV camera | `src/block_detected/io/camera/capture.py` | OS → app | Local device index |
| Ultralytics YOLO | `src/block_detected/detection/yolo/backend.py` | File → app | Local `.pt` only |
| PySide6/Qt | `src/block_detected/apps/gui/app.py` | OS display → user | Desktop GUI |
| TOML config | `src/block_detected/runtime/config_store.py` | Disk → app | Optional `block_detected.toml` |

**Protocol abstraction:**
- `DetectorBackend` Protocol in `src/block_detected/core/protocols.py` — allows swapping YOLO backend without changing `runtime/engine.py`; currently only `YoloDetector` is loaded via `src/block_detected/runtime/detector_loader.py`

## Ignored / adjacent artifacts (not runtime integrations)

- `wandb/` — gitignored; typical Ultralytics training export path, not used by GUI app
- `runs/` — gitignored; Ultralytics default output directory
- `graphify-out/` — local knowledge-graph tooling output (per workspace rules); not a runtime dependency
- `node_modules/` — stray artifact (contains `concurrently` shim); no root `package.json`; not part of Python stack

---

*Integration audit: 2026-06-05*

# Phase 9: Next.js + FastAPI Detection Console UI — Research

**Researched:** 2026-05-31  
**Domain:** Full-stack vision console (FastAPI streaming + WebSocket telemetry, Next.js App Router UI, Docker Compose)  
**Confidence:** HIGH (patterns verified against official FastAPI/Pydantic docs + existing `block_detected` codebase)

## Summary

Phase 9 wraps the existing `detect_block` pipeline in a FastAPI service with two concurrent output channels: an MJPEG video feed for the camera viewport and a WebSocket JSON telemetry stream for detection results, FPS, and latency. The Next.js frontend consumes both via env-configured URLs (`NEXT_PUBLIC_*`), stores live state in Zustand slices, and draws geometry overlays on a Canvas layer stacked over an `<img>` MJPEG element.

The critical backend architectural constraint is **single-process camera ownership**: OpenCV/picamera2 capture must happen in one background loop that publishes the latest BGR frame to MJPEG subscribers and runs `detect_block` off the event loop via `asyncio.to_thread`. Multiple MJPEG clients must read from shared memory, not open the camera per request. [CITED: https://github.com/fastapi/fastapi/issues/2956] [CITED: https://fastapi.tiangolo.com/advanced/custom-response/#streamingresponse]

Wire format uses **camelCase JSON** at the API boundary while keeping Python internals in snake_case aligned with `detection_contract.py`. Pydantic v2 `alias_generator=to_camel` plus `response_model_by_alias=True` (REST) and explicit `model_dump(by_alias=True)` (WebSocket) is the standard approach. [CITED: https://docs.pydantic.dev/2.1/usage/model_config/]

Recommended repo layout: sibling `frontend/` and `backend/` directories (no existing Next.js structure in repo), root `docker-compose.yml`, root `package.json` with `dev:all` via `concurrently`, and backend `requirements.txt` separate from Pi inference pins in `pyproject.toml`.

**Primary recommendation:** Backend-first wave — implement `DetectionLoopService` (capture → detect → broadcast) with mock `ImageSequenceFrameSource`, then scaffold Next.js UI against stable `/health`, `/video/stream`, and `/ws/detection` contracts.

<user_constraints>
## User Constraints (from CONTEXT.md)

### Locked Decisions

#### Frontend stack
- Next.js App Router, TypeScript, Tailwind CSS, Zustand
- Env vars only for URLs: `NEXT_PUBLIC_API_BASE_URL`, `NEXT_PUBLIC_WS_URL`, `NEXT_PUBLIC_STREAM_URL`
- No hardcoded localhost in components

#### Component architecture
Split into reusable components:
- `AppShell`, `Sidebar`, `TopStatusBar`, `CameraViewport`, `VisionOverlay`
- `DetectionControls`, `ClassificationPanel`, `PickupTelemetry`
- `CalibrationPanel`, `DatasetPanel`, `LogTerminal`

#### Zustand store slices
- connection status (disconnected / connected / error)
- FPS, latency
- detection mode, camera running state
- detection parameters (sliders)
- latest detection result
- logs (append-only terminal)

#### Vision overlay
- Canvas or SVG overlay on camera feed
- Draw: bounding box, four corners (TL/TR/BR/BL), center point, angle arrow, pickup pose text
- Overlay coordinates map from backend `cornersPx` / `centerPx` / `angleDeg`

#### Visual style
- Preserve `example_ui/real_time_detection_console_v2/code.html` dark cyber console
- Cyan primary `#4cd7f6`, emerald success, slate surfaces per `example_ui/precision_optic_interface/DESIGN.md`
- Side nav, top status bar, camera panel, parameter panel, telemetry panel
- Responsive at 1366×768 and desktop

#### Backend stack
- FastAPI, OpenCV, NumPy
- Inference: TFLite Runtime (preferred, matches project) or ONNX Runtime fallback
- Wrap existing `block_detected.pipeline.detect_block` and camera modules

#### API endpoints
| Method | Path | Purpose |
|--------|------|---------|
| GET | `/health` | System status |
| GET | `/video/stream` | MJPEG stream |
| WS | `/ws/detection` | Live telemetry JSON |
| POST | `/api/detection/start` | Start detection loop |
| POST | `/api/detection/stop` | Stop detection loop |
| POST | `/api/detection/params` | Update detection parameters |
| POST | `/api/calibration/save` | Save calibration |
| POST | `/api/dataset/save-frame` | Save frame to dataset |

#### Pydantic schemas (backend)
- `DetectionParams`, `DetectionResult`, `CornerPoint`, `PickupPose`
- `ClassificationScores`, `SystemStatus`

#### Frontend TypeScript contract (camelCase JSON wire format)
Must match backend output exactly:
- `blockId`, `confidence`, `centerPx`, `cornersPx`, `angleDeg`
- `pickupPoseMm`, `fps`, `latencyMs`, `valid`, `rejectReason`

Map from existing Python contract:
- `block_id` → `blockId`, `center_px` → `centerPx`, etc.
- `pickup_pose` → `pickupPoseMm` with `xMm`, `yMm`, `thetaDeg`
- `corners_px` → `cornersPx` with `tl`, `tr`, `br`, `bl` or array `[tl, tr, br, bl]`

#### Integration layer
- `frontend/lib/api.ts` — REST client
- `frontend/lib/ws.ts` — WebSocket with auto-reconnect
- `frontend/types/vision.ts` — shared types

#### Parameter UX
- Sliders update Zustand immediately
- Debounced POST to `/api/detection/params` (300–500ms)

#### Mock mode
- Backend env `MOCK_CAMERA=true` or `DETECTION_MODE=mock`
- Stable fake detection data when no camera/model
- Clear `# TODO:` comments at mock injection points

#### DevOps
- `docker-compose.yml`: `frontend`, `backend`, optional `nginx`
- Healthchecks on both services
- Root command: `npm run dev:all` OR `make dev` starts Next.js + FastAPI locally
- `.env.example` with all required variables
- README section: local dev, Raspberry Pi deploy, mock vs real camera toggle

### Claude's Discretion
- Exact Next.js directory layout (`frontend/` vs repo root) — prefer `frontend/` + `backend/` siblings if no existing structure
- Wave split for plans (backend-first vs parallel frontend scaffold)
- nginx config details (optional service)
- Debounce interval exact value
- SVG vs Canvas for overlay (Canvas preferred for performance)

### Deferred Ideas (OUT OF SCOPE)
- OPS-01 live tuning beyond current slider set (v2)
- RUN-01 multi-block scene graph (v2)
- RUN-02 temporal filtering (v2)
- nginx TLS termination (production hardening, not v1 console)
</user_constraints>

<phase_requirements>
## Phase Requirements

Phase 9 is not yet mapped to formal REQ IDs in `REQUIREMENTS.md`. Success criteria derive from CONTEXT and roadmap Phase 9 goal. Planner should treat these as phase acceptance behaviors:

| ID | Description | Research Support |
|----|-------------|------------------|
| UI-09-01 | Operator sees live MJPEG camera feed at 640×480 in browser | MJPEG `StreamingResponse` + `<img src={STREAM_URL}>` pattern |
| UI-09-02 | WebSocket delivers FPS, latency, latest detection JSON | ConnectionManager broadcast from detection loop |
| UI-09-03 | Canvas overlay draws corners/center/angle from telemetry | Coordinate scale 640×480 → display size via ResizeObserver |
| UI-09-04 | All control buttons hit real REST endpoints (no dead UI) | REST client + backend start/stop/params routes |
| UI-09-05 | Mock mode works without camera/model on dev machine | `ImageSequenceFrameSource` + env toggle |
| UI-09-06 | `docker compose up` runs frontend + backend with healthchecks | Compose multi-service pattern |
| UI-09-07 | `npm run dev:all` or `make dev` runs both servers locally | `concurrently` root script |
| UI-09-08 | Wire JSON camelCase matches TypeScript types exactly | Pydantic `to_camel` + shared schema fixtures |
</phase_requirements>

## Standard Stack

### Core

| Library | Version | Purpose | Why Standard |
|---------|---------|---------|--------------|
| Next.js | 16.2.6 | App Router frontend | Current stable; App Router is locked decision [VERIFIED: npm registry 2026-05-31] |
| React | 19.x (bundled with Next) | UI runtime | Next 16 default |
| TypeScript | 5.x | Typed frontend contract | Standard with Next scaffold |
| Tailwind CSS | 4.3.0 | Cyber-console styling | Matches reference HTML utility approach [VERIFIED: npm registry] |
| Zustand | 5.0.14 | Client state slices | Lightweight; works with App Router client components [VERIFIED: npm registry] |
| FastAPI | 0.136.3 | REST + WebSocket + streaming | Official patterns for WS + StreamingResponse [VERIFIED: PyPI; CITED: fastapi.tiangolo.com] |
| Uvicorn | 0.48.0 | ASGI server | FastAPI default; use `--workers 1` when holding camera [VERIFIED: PyPI] |
| Pydantic | 2.13.4 | Wire schemas + validation | v2 `to_camel` alias generator [VERIFIED: PyPI] |
| OpenCV (`opencv-python-headless`) | ≥4.11,<4.14 | MJPEG encode, frame read | Matches existing project pin; headless for Docker [VERIFIED: pyproject.toml] |
| NumPy | ≥2,<3 | Frame buffers | Existing project constraint |
| block_detected (local) | 0.1.0 | `detect_block`, camera, contract | Wrap, do not rewrite |

### Supporting

| Library | Version | Purpose | When to Use |
|---------|---------|---------|-------------|
| `concurrently` | 10.0.0 | Run Next + Uvicorn in one terminal | Root `dev:all` script [VERIFIED: npm registry] |
| `python-multipart` | latest | FastAPI form uploads | Dataset save-frame if multipart |
| `httpx` | latest | Async API tests | Backend pytest with `AsyncClient` |
| `websockets` | latest | FastAPI WS dependency | Required by Starlette WS stack [CITED: fastapi.tiangolo.com/advanced/websockets/] |
| `tflite-runtime` | 2.14.0 | Pi inference | Pi deploy only; dev may use stub classifier |
| nginx (optional) | alpine | Reverse proxy | Single-origin dev/prod when enabled |

### Alternatives Considered

| Instead of | Could Use | Tradeoff |
|------------|-----------|----------|
| MJPEG over HTTP | WebRTC / HLS | MJPEG is simplest for `<img>` tag; locked by CONTEXT UX |
| Frontend canvas overlay | Backend-drawn MJPEG | CONTEXT prefers frontend canvas; backend overlay duplicates work |
| Next.js rewrites to proxy API | Direct env URLs | CONTEXT forbids hardcoded localhost; env URLs + CORS is explicit |
| Redis pub/sub for WS | In-memory ConnectionManager | v1 single-process Pi/console; Redis only if multi-worker |

**Installation (backend dev):**
```bash
cd backend
python3 -m venv .venv && source .venv/bin/activate
pip install "fastapi>=0.136" "uvicorn[standard]>=0.48" "pydantic>=2.13" \
  "opencv-python-headless>=4.11,<4.14" "numpy>=2,<3" "python-multipart" "websockets"
pip install -e ..   # editable block_detected from repo root
```

**Installation (frontend dev):**
```bash
cd frontend
npm install next@16 react react-dom zustand tailwindcss @tailwindcss/postcss
npm install -D typescript @types/node @types/react concurrently
```

## Architecture Patterns

### Recommended Project Structure

```
block_detected/                 # existing Python package (unchanged core)
frontend/
  app/                          # Next.js App Router pages
  components/                   # AppShell, CameraViewport, VisionOverlay, ...
  lib/
    api.ts                      # REST client (uses NEXT_PUBLIC_API_BASE_URL)
    ws.ts                       # WebSocket + reconnect
  stores/
    useVisionStore.ts           # Zustand slices
  types/
    vision.ts                   # camelCase TS interfaces
backend/
  app/
    main.py                     # FastAPI app, CORS, lifespan
    routes/
      health.py
      detection.py
      stream.py
      calibration.py
      dataset.py
    services/
      detection_loop.py         # capture + detect + publish
      frame_source_factory.py   # mock/real camera selection
    schemas/
      wire.py                   # Pydantic camelCase models
    ws/
      manager.py                # ConnectionManager
  requirements.txt
docker-compose.yml
docker-compose.dev.yml          # optional bind-mount overrides
package.json                    # root: dev:all script
Makefile                        # optional: make dev
.env.example
```

### Pattern 1: Producer–Consumer Detection Loop (single camera owner)

**What:** One asyncio background task owns `FrameSource`, stores latest BGR frame in a thread-safe slot, runs `detect_block` in `asyncio.to_thread`, broadcasts telemetry.

**When to use:** Always — OpenCV cannot safely open camera per HTTP client. [CITED: https://github.com/fastapi/fastapi/issues/2956]

**Example:**
```python
# Source: FastAPI StreamingResponse docs + OpenCV MJPEG community pattern
# CITED: https://fastapi.tiangolo.com/advanced/custom-response/#streamingresponse

class DetectionLoopService:
    def __init__(self) -> None:
        self._latest_jpeg: bytes | None = None
        self._latest_telemetry: DetectionTelemetryWire | None = None
        self._running = False

    async def run(self) -> None:
        source = create_frame_source_from_env()
        source.start()
        try:
            while self._running:
                t0 = time.perf_counter()
                frame = await asyncio.to_thread(source.read)
                result = await asyncio.to_thread(detect_block, frame, self._settings)
                jpeg = await asyncio.to_thread(encode_jpeg, frame.image_bgr)
                self._latest_jpeg = jpeg
                telemetry = build_telemetry(result, t0)
                self._latest_telemetry = telemetry
                await ws_manager.broadcast(telemetry.model_dump(by_alias=True))
                await asyncio.sleep(max(0.0, (1 / 30) - (time.perf_counter() - t0)))
        finally:
            source.stop()

def encode_jpeg(bgr: np.ndarray, quality: int = 80) -> bytes:
    ok, buf = cv2.imencode(".jpg", bgr, [cv2.IMWRITE_JPEG_QUALITY, quality])
    if not ok:
        raise RuntimeError("JPEG encode failed")
    return buf.tobytes()
```

### Pattern 2: MJPEG Stream Endpoint

**What:** Async generator yields multipart frames from shared latest JPEG bytes.

**When to use:** `GET /video/stream` — browser displays via `<img>` without WebRTC.

**Example:**
```python
# CITED: https://fastapi.tiangolo.com/advanced/custom-response/#streamingresponse
# CITED: https://github.com/fastapi/fastapi/issues/2956 (shared frame, not per-client capture)

@app.get("/video/stream")
async def video_stream(request: Request):
    async def generate():
        while True:
            if await request.is_disconnected():
                break
            jpeg = loop_service.latest_jpeg()
            if jpeg:
                yield (
                    b"--frame\r\n"
                    b"Content-Type: image/jpeg\r\n\r\n" + jpeg + b"\r\n"
                )
            await asyncio.sleep(1 / 30)

    return StreamingResponse(
        generate(),
        media_type="multipart/x-mixed-replace; boundary=frame",
        headers={"Cache-Control": "no-cache, no-store", "X-Accel-Buffering": "no"},
    )
```

Use `opencv-python-headless` in Docker; run Uvicorn with **`--workers 1`** when camera or in-memory WS manager is process-local. [ASSUMED: Pi/console v1 is single-process; multi-worker needs Redis pub/sub]

### Pattern 3: WebSocket Telemetry Broadcast

**What:** FastAPI official `ConnectionManager` accepts clients on `/ws/detection`; detection loop pushes JSON telemetry.

**When to use:** Live FPS, latency, detection result updates.

**Example:**
```python
# CITED: https://fastapi.tiangolo.com/advanced/websockets/ (ConnectionManager)

class ConnectionManager:
    def __init__(self) -> None:
        self.active_connections: list[WebSocket] = []

    async def connect(self, websocket: WebSocket) -> None:
        await websocket.accept()
        self.active_connections.append(websocket)

    def disconnect(self, websocket: WebSocket) -> None:
        if websocket in self.active_connections:
            self.active_connections.remove(websocket)

    async def broadcast_json(self, payload: dict) -> None:
        dead: list[WebSocket] = []
        for ws in self.active_connections:
            try:
                await ws.send_json(payload)
            except Exception:
                dead.append(ws)
        for ws in dead:
            self.disconnect(ws)

@app.websocket("/ws/detection")
async def ws_detection(websocket: WebSocket):
    await manager.connect(websocket)
    try:
        while True:
            await websocket.receive_text()  # optional client ping; ignore or handle
    except WebSocketDisconnect:
        manager.disconnect(websocket)
```

Telemetry envelope (recommended):
```json
{
  "type": "telemetry",
  "fps": 28.4,
  "latencyMs": 14.2,
  "valid": true,
  "rejectReason": null,
  "detection": { "blockId": 1, "confidence": 0.94, "status": "ok", ... },
  "classificationScores": { "block01": 0.94, "block02": 0.02, "block03": 0.02, "block04": 0.02 }
}
```

### Pattern 4: Next.js Env-Based API Client + Zustand

**What:** Client components read `process.env.NEXT_PUBLIC_*`; Zustand store updated from WebSocket module via `getState()`.

**When to use:** All frontend data fetching; avoids Next rewrites (CONTEXT uses explicit backend URLs).

**Example:**
```typescript
// frontend/lib/api.ts
const API_BASE = process.env.NEXT_PUBLIC_API_BASE_URL;
if (!API_BASE) throw new Error("NEXT_PUBLIC_API_BASE_URL is required");

export async function postDetectionParams(params: DetectionParamsWire) {
  const res = await fetch(`${API_BASE}/api/detection/params`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(params),
  });
  if (!res.ok) throw new Error(await res.text());
}

// frontend/lib/ws.ts — update store outside React
import { useVisionStore } from "@/stores/useVisionStore";

export function connectDetectionWs() {
  const url = process.env.NEXT_PUBLIC_WS_URL!;
  const ws = new WebSocket(url);
  ws.onmessage = (ev) => {
    const msg = JSON.parse(ev.data);
    useVisionStore.getState().applyTelemetry(msg);
  };
  ws.onopen = () => useVisionStore.getState().setConnection("connected");
  ws.onclose = () => { useVisionStore.getState().setConnection("disconnected"); scheduleReconnect(); };
  return ws;
}
```

Use `'use client'` on interactive components. App Router server components must not import Zustand hooks. [CITED: Zustand + Next.js App Router guidance — noqta.tn 2026 tutorial; MEDIUM confidence for store-factory pattern on SSR-heavy apps]

Debounced params: `useDebouncedCallback` (~400ms) or lodash debounce in `DetectionControls`.

### Pattern 5: Canvas Overlay on MJPEG `<img>`

**What:** Stack absolute-positioned `<canvas>` over `<img src={STREAM_URL}>`. Map backend pixel coords (640×480) to displayed size.

**When to use:** `VisionOverlay` — corners, bbox, center, angle arrow, pickup text.

**Example:**
```typescript
// CITED: MDN/HTML overlay pattern; Stack Overflow MJPEG + canvas redraw loop
"use client";

function scalePoint(p: PointPx, img: HTMLImageElement, canvas: HTMLCanvasElement) {
  const sx = canvas.width / 640;  // contract locked resolution
  const sy = canvas.height / 480;
  return { x: p.x * sx, y: p.y * sy };
}

function drawOverlay(ctx: CanvasRenderingContext2D, det: DetectionWire, img: HTMLImageElement, canvas: HTMLCanvasElement) {
  ctx.clearRect(0, 0, canvas.width, canvas.height);
  if (!det.valid || !det.cornersPx) return;
  const tl = scalePoint(det.cornersPx.tl, img, canvas);
  // ... tr, br, bl
  ctx.strokeStyle = "#4cd7f6";
  ctx.beginPath();
  ctx.moveTo(tl.x, tl.y);
  // close quad TL→TR→BR→BL→TL
  ctx.stroke();
  // center + angle arrow from angleDeg
}

// ResizeObserver keeps canvas sized to img container
// requestAnimationFrame loop redraws overlay when telemetry updates (MJPEG img updates natively)
```

**Do not** draw MJPEG into canvas for display unless post-processing is required — CONTEXT uses `<img>` for video and canvas for vectors only. [CITED: https://stackoverflow.com/questions/13500558/motion-jpeg-in-html5-canvas]

### Pattern 6: Mock Camera via `ImageSequenceFrameSource`

**What:** Backend factory selects frame source from env/config; mock path uses existing camera module.

**When to use:** Dev machines without USB/Pi camera; CI smoke tests.

**Example:**
```python
# Wrap existing block_detected.camera — VERIFIED: src/block_detected/camera.py

def create_frame_source_from_env() -> FrameSource:
    if os.getenv("MOCK_CAMERA", "").lower() in {"1", "true", "yes"}:
        settings = load_camera_settings("config/camera.example.json", profile="image_sequence")
        return ImageSequenceFrameSource(settings)  # tests/fixtures/frames
    return create_frame_source(load_active_camera_settings())

# TODO: inject synthetic stable telemetry when DETECTION_MODE=mock and detect fails
```

Existing `detect_block` synthetic hooks (`__block_detected_synthetic__` in frame mapping) can force deterministic telemetry in unit tests without images. [VERIFIED: src/block_detected/pipeline.py]

### Pattern 7: Docker Compose (frontend + backend + optional nginx)

**What:** Two required services with healthchecks; nginx optional third service for single-origin proxy.

**Example:**
```yaml
# docker-compose.yml (sketch)
services:
  backend:
    build: ./backend
    ports: ["8000:8000"]
    environment:
      MOCK_CAMERA: "true"
      CAMERA_CONFIG: /app/config/camera.example.json
    volumes:
      - ./config:/app/config:ro
      - ./tests/fixtures/frames:/app/fixtures:ro
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8000/health"]
      interval: 10s
      timeout: 5s
      retries: 5
    command: uvicorn app.main:app --host 0.0.0.0 --port 8000 --workers 1

  frontend:
    build: ./frontend
    ports: ["3000:3000"]
    environment:
      NEXT_PUBLIC_API_BASE_URL: http://localhost:8000
      NEXT_PUBLIC_WS_URL: ws://localhost:8000/ws/detection
      NEXT_PUBLIC_STREAM_URL: http://localhost:8000/video/stream
    depends_on:
      backend:
        condition: service_healthy

  nginx:  # optional — Claude's discretion
    image: nginx:alpine
    ports: ["8080:80"]
    depends_on: [frontend, backend]
    # proxy / → frontend:3000, /video /ws /api /health → backend:8000
    # proxy_buffering off for MJPEG; Upgrade headers for WS
```

Dev compose variant: bind-mount `./backend/app` and `./frontend`, enable `--reload` / `next dev`.

### Pattern 8: Local Dev Orchestration

**Root `package.json`:**
```json
{
  "scripts": {
    "dev:all": "concurrently -n backend,frontend -c blue,green \"npm run dev:backend\" \"npm run dev:frontend\"",
    "dev:backend": "cd backend && .venv/bin/uvicorn app.main:app --reload --port 8000",
    "dev:frontend": "cd frontend && next dev --port 3000"
  },
  "devDependencies": {
    "concurrently": "^10.0.0"
  }
}
```

**Makefile alternative:**
```makefile
dev:
\tconcurrently -n api,web "cd backend && uvicorn app.main:app --reload --port 8000" "cd frontend && npm run dev"
```

Enable FastAPI CORS for `http://localhost:3000` (and Docker frontend origin). [CITED: Next.js + FastAPI integration guides — codevoweb.com 2026; MEDIUM confidence]

### Anti-Patterns to Avoid

- **Per-request `VideoCapture(0)` in MJPEG handler:** Second client breaks first; use shared loop. [CITED: fastapi#2956]
- **Multiple Uvicorn workers with in-memory WS manager:** Clients miss broadcasts; stay at 1 worker or add Redis.
- **Hardcoded `localhost:8000` in React components:** Violates CONTEXT; use env vars.
- **Rewriting core `detect_block` logic in FastAPI routes:** Wrap `PipelineSettings` + existing modules only.
- **Blocking `cv2.imencode` on event loop:** Use `asyncio.to_thread`.
- **Deleting/modifying `example_ui/`:** Reference only per CONTEXT.

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| snake_case ↔ camelCase mapping | Manual dict transforms | Pydantic v2 `to_camel` + `model_dump(by_alias=True)` | Field drift breaks TS contract |
| Corner ordering / validation | Custom geometry in API layer | `detection_contract.validate_detection_result` | Contract already enforced |
| Camera backends | New capture abstraction | `create_frame_source`, `ImageSequenceFrameSource` | Phase 2 complete |
| MJPEG multipart framing | Third-party stream server | `StreamingResponse` + boundary `--frame` | 10-line standard pattern |
| WebSocket connection registry | Custom pub/sub | FastAPI `ConnectionManager` | Documented, sufficient for v1 |
| Debounced slider POST | Global event bus | `useDebouncedCallback` / lodash debounce | One-liner UX pattern |

**Key insight:** The console is a thin wrapper — all vision truth stays in `block_detected`; FastAPI only orchestrates I/O and serializes wire JSON.

## Common Pitfalls

### Pitfall 1: MJPEG Works Once, Breaks With Second Tab
**What goes wrong:** Each stream handler opens camera independently.  
**Why it happens:** OpenCV single-capture constraint. [CITED: fastapi#2956]  
**How to avoid:** Single detection loop publishes `latest_jpeg`; stream handlers read shared bytes.  
**Warning signs:** `terminating async callback` warnings in OpenCV logs.

### Pitfall 2: WebSocket Connects but No Telemetry
**What goes wrong:** WS accepts connections but nothing sent until `/api/detection/start`.  
**Why it happens:** Loop not started by default vs UI expects live data on load.  
**How to avoid:** Document startup sequence; optionally auto-start in dev/mock; TopStatusBar reflects idle vs running.  
**Warning signs:** FPS stays 0, overlay empty while MJPEG still flows.

### Pitfall 3: Overlay Coordinates Misaligned
**What goes wrong:** Corners drift from block when panel resized.  
**Why it happens:** Canvas CSS size ≠ backing store; object-fit letterboxing ignored.  
**How to avoid:** ResizeObserver on container; compute letterbox offsets; scale from 640×480 source space.  
**Warning signs:** Correct at one window size, wrong when resized.

### Pitfall 4: CORS / Mixed Content
**What goes wrong:** Browser blocks fetch/WebSocket from `:3000` to `:8000`.  
**Why it happens:** Cross-origin without CORS; `ws://` vs `wss://` mismatch in prod.  
**How to avoid:** `CORSMiddleware` on FastAPI; env vars switch scheme per environment.  
**Warning signs:** Network tab shows CORS error or WS failed.

### Pitfall 5: Pydantic Wire vs Contract Field Names
**What goes wrong:** TS expects `pickupPoseMm` but API emits `pickup_pose`.  
**Why it happens:** Forgot `by_alias=True` on responses / WS dumps.  
**How to avoid:** Base wire model with explicit field aliases; golden JSON fixture test.  
**Warning signs:** Frontend parses `undefined` for nested pose fields.

### Pitfall 6: Docker Frontend Calling `localhost:8000` Inside Container
**What goes wrong:** Browser on host works; server-side fetch from Next container fails.  
**Why it happens:** `localhost` inside container ≠ host backend.  
**How to avoid:** CONTEXT uses client-side fetch only for API/WS/stream; no SSR fetch to backend in v1.  
**Warning signs:** SSR errors referencing connection refused to :8000.

### Pitfall 7: Classification Panel Empty
**What goes wrong:** `DetectionResult` has no per-class score array.  
**Why it happens:** Contract exposes single `confidence`, not 4-class vector.  
**How to avoid:** Extend telemetry-only `ClassificationScores` from classifier internals in loop; stub equal splits in mock mode with `# TODO`.  
**Warning signs:** Panel wired but always blank on real pipeline.

## Code Examples

### Pydantic camelCase Wire Models

```python
# CITED: https://docs.pydantic.dev/2.1/usage/model_config/
from pydantic import BaseModel, ConfigDict, Field
from pydantic.alias_generators import to_camel

class WireModel(BaseModel):
    model_config = ConfigDict(
        alias_generator=to_camel,
        populate_by_name=True,
    )

class PointWire(WireModel):
    x: float
    y: float

class CornersWire(WireModel):
    tl: PointWire
    tr: PointWire
    br: PointWire
    bl: PointWire

class PickupPoseWire(WireModel):
    x_mm: float = Field(serialization_alias="xMm")
    y_mm: float = Field(serialization_alias="yMm")
    theta_deg: float = Field(serialization_alias="thetaDeg")

class DetectionResultWire(WireModel):
    block_id: int | None = Field(default=None, serialization_alias="blockId")
    confidence: float
    center_px: PointWire | None = Field(default=None, serialization_alias="centerPx")
    corners_px: CornersWire | None = Field(default=None, serialization_alias="cornersPx")
    angle_deg: float | None = Field(default=None, serialization_alias="angleDeg")
    pickup_pose: PickupPoseWire | None = Field(default=None, serialization_alias="pickupPoseMm")
    status: str
    valid: bool
    reject_reason: str | None = Field(default=None, serialization_alias="rejectReason")

def from_contract(result: DetectionResult, fps: float, latency_ms: float) -> DetectionTelemetryWire:
    # Map dataclass → wire; set valid=(status==ok), reject_reason from debug
    ...
```

Use explicit `serialization_alias` for abbreviated wire names (`pickupPoseMm`, `xMm`) where `to_camel` alone yields `pickupPose`, `xMm` from `x_mm` — verify each field against CONTEXT table.

FastAPI route:
```python
@app.get("/health", response_model=SystemStatusWire, response_model_by_alias=True)
async def health(): ...
```

### Mapping from `detection_contract.py`

Existing serializer for snake_case baseline:
```python
# VERIFIED: src/block_detected/detection_contract.py
from block_detected.detection_contract import result_to_dict, DetectionResult

payload_snake = result_to_dict(result)
# Transform in wire builder — do not change contract module for camelCase
```

Recommended corner wire shape (planner lock): **named keys** `{ tl, tr, br, bl }` each `{ x, y }` — matches TL/TR/BR/BL semantics and TypeScript readability.

### FastAPI Lifespan + CORS

```python
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

@asynccontextmanager
async def lifespan(app: FastAPI):
    # optionally defer loop start to POST /api/detection/start
    yield
    await detection_loop.stop()

app = FastAPI(lifespan=lifespan)
app.add_middleware(
    CORSMiddleware,
    allow_origins=os.getenv("CORS_ORIGINS", "http://localhost:3000").split(","),
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
```

## State of the Art

| Old Approach | Current Approach | When Changed | Impact |
|--------------|------------------|--------------|--------|
| Static HTML console in `example_ui/` | Next.js componentized App Router | Phase 9 | Production UI with typed contract |
| CLI / pytest-only observation | WebSocket telemetry + MJPEG | Phase 9 | Operator-facing runtime visibility |
| Pydantic v1 `Config` class | Pydantic v2 `model_config = ConfigDict(...)` | Pydantic 2.0+ | Use v2 patterns in backend |
| Next.js Pages API proxy | Env-based direct backend URLs + CORS | CONTEXT lock | Simpler Docker/Pi deploy |

**Deprecated/outdated:**
- Do not use Next.js API routes as primary Python host (Vercel starter pattern) — this project uses separate FastAPI service on Pi/dev.
- Do not use `picamera` legacy library — use existing `PiCamera2FrameSource`. [VERIFIED: CLAUDE.md / camera.py]

## Assumptions Log

| # | Claim | Section | Risk if Wrong |
|---|-------|---------|---------------|
| A1 | Uvicorn `--workers 1` sufficient for v1 Pi console | MJPEG pattern | Multi-worker breaks WS broadcast |
| A2 | `to_camel` + explicit aliases cover all CONTEXT wire names | Pydantic mapping | TS/backend JSON mismatch |
| A3 | Classification 4-class scores available from classifier internals | Telemetry | Panel empty until classifier API extended |
| A4 | Client-side-only API calls (no SSR backend fetch) | Next.js pattern | Docker networking confusion |
| A5 | Next.js 16.x acceptable despite project not previously pinning frontend | Standard Stack | Minor breaking changes vs 15 |

## Open Questions (RESOLVED)

1. **Classification scores source** — **RESOLVED:** Optional `classificationScores` on telemetry wire; mock `{block01:0.25, block02:0.25, block03:0.25, block04:0.25}` when classifier has no softmax vector; real scores when `classifier.py` exposes them (`# TODO` at injection point in Plan 03).

2. **Auto-start detection loop on backend boot?** — **RESOLVED:** Idle by default; auto-start only when `MOCK_CAMERA=true` OR `DETECTION_MODE=mock` (lifespan hook in Plan 03). Real camera requires explicit POST `/api/detection/start`.

3. **nginx in v1 compose?** — **RESOLVED:** Deferred. Plan 07 includes commented optional Compose profile only; dev uses direct ports + `CORS_ORIGINS`. TLS/nginx is production hardening, out of v1 scope.

## Environment Availability

| Dependency | Required By | Available | Version | Fallback |
|------------|-------------|-----------|---------|----------|
| Node.js | Next.js frontend | ✓ | v24.14.0 | — |
| npm | frontend packages | ✓ | 11.9.0 | pnpm/yarn |
| Python | FastAPI backend | ✓ | 3.14.4 (dev); target ≥3.11 Pi | 3.11 venv on Pi |
| Docker | Compose deploy | ✓ | 29.3.0 | local `dev:all` without Docker |
| FastAPI/uvicorn | backend | ✗ (not in default env) | — | `pip install` in backend venv |
| pytest | backend tests | ✓ | 9.0.3 (.venv) | — |
| OpenCV | MJPEG + pipeline | ✓ (dev extra) | via pyproject dev | opencv-python-headless in Docker |
| Pi camera / USB | real camera mode | ✗ on dev Mac | — | `MOCK_CAMERA=true` + image_sequence |
| tflite-runtime | Pi real inference | ✗ on dev Mac | — | classifier stub backend |

**Missing dependencies with no fallback:**
- None for mock-mode development (image_sequence fixtures exist at `tests/fixtures/frames` per `config/camera.example.json`).

**Missing dependencies with fallback:**
- Physical camera → `ImageSequenceFrameSource`
- TFLite model → classifier stub (`config/classifier.example.json`)

## Validation Architecture

### Test Framework

| Property | Value |
|----------|-------|
| Framework | pytest 9.x (backend); Vitest/Jest TBD (frontend) |
| Config file | `pyproject.toml` `[tool.pytest.ini_options]` |
| Quick run command | `pytest tests/test_api_health.py -x` (Wave 0 create) |
| Full suite command | `pytest tests/ -q` |

### Phase Requirements → Test Map

| Req ID | Behavior | Test Type | Automated Command | File Exists? |
|--------|----------|-----------|-------------------|-------------|
| UI-09-01 | MJPEG endpoint returns multipart stream | integration | `pytest tests/test_api_stream.py::test_mjpeg_content_type -x` | ❌ Wave 0 |
| UI-09-02 | WebSocket emits telemetry JSON | integration | `pytest tests/test_api_ws.py::test_ws_telemetry_after_start -x` | ❌ Wave 0 |
| UI-09-05 | Mock mode uses image sequence | unit | `pytest tests/test_frame_source_factory.py::test_mock_camera -x` | ❌ Wave 0 |
| UI-09-08 | camelCase wire matches fixture | unit | `pytest tests/test_wire_schema.py::test_golden_detection_json -x` | ❌ Wave 0 |
| CONT-01 | Wrapped detect_block unchanged | regression | `pytest tests/test_integration_pipeline.py -x` | ✅ |
| UI-09-06 | Docker healthchecks | smoke/manual | `docker compose up --wait` | ❌ Wave 0 |

### Sampling Rate

- **Per task commit:** `pytest tests/test_api_*.py -x` (backend tasks); `npm run lint` (frontend tasks)
- **Per wave merge:** `pytest tests/ -q` + existing 50 pipeline tests
- **Phase gate:** Full pytest green; manual UAT: browser shows MJPEG + overlay + WS FPS

### Wave 0 Gaps

- [ ] `backend/requirements.txt` — FastAPI stack pins
- [ ] `tests/test_api_health.py` — `/health` JSON + camelCase
- [ ] `tests/test_api_stream.py` — MJPEG headers, reads first boundary
- [ ] `tests/test_api_ws.py` — Starlette/FastAPI WebSocket test client
- [ ] `tests/test_wire_schema.py` — golden camelCase fixture vs TS sample
- [ ] `tests/fixtures/wire/detection_success.json` — shared golden file
- [ ] Frontend test runner decision (Vitest recommended; optional for v1)
- [ ] Root `package.json` with `dev:all`

## Security Domain

### Applicable ASVS Categories

| ASVS Category | Applies | Standard Control |
|---------------|---------|------------------|
| V2 Authentication | no | v1 local console; no auth |
| V3 Session Management | no | — |
| V4 Access Control | no | LAN/dev only in v1 |
| V5 Input Validation | yes | Pydantic wire models on all POST bodies |
| V6 Cryptography | no | TLS deferred with nginx TLS |

### Known Threat Patterns for Stack

| Pattern | STRIDE | Standard Mitigation |
|---------|--------|---------------------|
| Unvalidated detection params | Tampering | Pydantic bounds on thresholds/areas |
| Path traversal on dataset save | Elevation | Confine saves to configured dataset dir |
| CORS wildcard in production | Spoofing | Explicit `CORS_ORIGINS` env list |
| oversized POST bodies | DoS | FastAPI/Starlette default limits; cap upload size on save-frame |

## Project Constraints (from CLAUDE.md / workspace rules)

- Wrap existing `detect_block` — do not rewrite pipeline logic
- No ArUco markers
- TFLite INT8 preferred on Pi; stub acceptable in dev
- 640×480 locked capture resolution (`TARGET_SHAPE` in camera module)
- GSD workflow: phase work via `/gsd-execute-phase` or `/gsd-quick`
- Do not delete/modify `example_ui/` (reference only)
- Pi camera: picamera2 apt path, not OpenCV VideoCapture on Pi 5

## Sources

### Primary (HIGH confidence)
- [FastAPI StreamingResponse](https://fastapi.tiangolo.com/advanced/custom-response/#streamingresponse) — MJPEG streaming pattern
- [FastAPI WebSockets + ConnectionManager](https://fastapi.tiangolo.com/advanced/websockets/) — broadcast, disconnect handling
- [Pydantic v2 model config / alias_generator](https://docs.pydantic.dev/2.1/usage/model_config/) — `to_camel`, `populate_by_name`
- `src/block_detected/detection_contract.py` — contract fields, `result_to_dict`
- `src/block_detected/pipeline.py` — `detect_block`, synthetic mock hooks
- `src/block_detected/camera.py` — `ImageSequenceFrameSource`, `create_frame_source`
- `config/camera.example.json` — mock image_sequence profile

### Secondary (MEDIUM confidence)
- [FastAPI GitHub #2956](https://github.com/fastapi/fastapi/issues/2956) — single camera capture constraint
- [Stack Overflow: MJPEG in canvas](https://stackoverflow.com/questions/13500558/motion-jpeg-in-html5-canvas) — img vs canvas roles
- Next.js + FastAPI concurrently dev guides (codevoweb.com, Vercel starter docs)
- Docker Compose healthcheck patterns (DEV Community 2026)

### Tertiary (LOW confidence — flag for validation)
- Zustand App Router store-factory pattern (noqta.tn 2026) — validate during frontend scaffold
- nginx MJPEG `proxy_buffering off` — standard but not verified against this repo yet

## Metadata

**Confidence breakdown:**
- Standard stack: HIGH — versions verified via npm/PyPI; FastAPI/Pydantic patterns from official docs
- Architecture: HIGH — aligns with existing camera/pipeline modules and official WS/stream patterns
- Pitfalls: MEDIUM-HIGH — MJPEG/camera issues well-documented; overlay letterboxing needs UI QA

**Research date:** 2026-05-31  
**Valid until:** 2026-06-30 (frontend semver may move faster — re-verify Next.js pin at implementation)

---

## RESEARCH COMPLETE

**Phase:** 09 - Next.js + FastAPI detection console UI  
**Confidence:** HIGH

### Key Findings
- Use a **single detection loop** as camera owner; MJPEG and WebSocket are consumers of shared latest frame/telemetry — never open camera per HTTP client.
- **Pydantic v2 `to_camel`** with explicit aliases for `pickupPoseMm` / `xMm` fields maps `detection_contract.py` to the locked TypeScript wire format.
- **Mock mode** should reuse `ImageSequenceFrameSource` + `config/camera.example.json` profile, not a parallel fake pipeline.
- Frontend: **`<img>` for MJPEG + absolute Canvas overlay** with 640×480→display scaling; Zustand updated from WS via `getState()` outside React.
- Run Uvicorn with **`--workers 1`**; root **`concurrently`** script or Makefile for local dev; Docker Compose with `/health` healthchecks on both services.

### File Created
`.planning/phases/09-next-js-fastapi-detection-console-ui-with-websocket-telemetr/09-RESEARCH.md`

### Confidence Assessment
| Area | Level | Reason |
|------|-------|--------|
| Standard Stack | HIGH | npm/PyPI versions verified; official FastAPI/Pydantic docs |
| Architecture | HIGH | Matches existing Python modules + documented streaming/WS patterns |
| Pitfalls | MEDIUM-HIGH | Camera/overlay issues documented; classifier scores need planner decision |

### Open Questions (RESOLVED)
- ClassificationScores: optional wire field; mock 0.25 split or classifier vector when available
- Auto-start: only when MOCK_CAMERA/DETECTION_MODE=mock; else explicit START
- nginx: deferred; comment-only optional profile in Plan 07

### Ready for Planning
Research complete. Planner can now create PLAN.md files.

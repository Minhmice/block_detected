# Phase 9: Next.js + FastAPI Detection Console UI — Context

**Gathered:** 2026-05-31
**Status:** Ready for planning
**Source:** User specification (prior session)

<domain>
## Phase Boundary

Convert the static HTML reference UI in `example_ui/` into a production Next.js + TypeScript + Tailwind frontend connected to a new FastAPI backend that wraps the existing `block_detected` Python pipeline.

**In scope:**
- Next.js App Router frontend with Zustand state, componentized cyber-console UI
- FastAPI backend: health, MJPEG stream, WebSocket telemetry, detection/calibration/dataset REST endpoints
- Shared typed contract (Python Pydantic ↔ TypeScript) aligned with existing `detection_contract.py`
- Docker Compose (frontend + backend + optional nginx), local dev orchestration (`npm run dev:all` or `make dev`)
- Mock mode when camera/model unavailable

**Out of scope:**
- Deleting or modifying `example_ui/` (reference only)
- Replacing the core `detect_block` pipeline logic (wrap, don't rewrite)
- v2 requirements (multi-block, temporal tracking, template fallback)

</domain>

<decisions>
## Implementation Decisions

### Frontend stack
- Next.js App Router, TypeScript, Tailwind CSS, Zustand
- Env vars only for URLs: `NEXT_PUBLIC_API_BASE_URL`, `NEXT_PUBLIC_WS_URL`, `NEXT_PUBLIC_STREAM_URL`
- No hardcoded localhost in components

### Component architecture
Split into reusable components:
- `AppShell`, `Sidebar`, `TopStatusBar`, `CameraViewport`, `VisionOverlay`
- `DetectionControls`, `ClassificationPanel`, `PickupTelemetry`
- `CalibrationPanel`, `DatasetPanel`, `LogTerminal`

### Zustand store slices
- connection status (disconnected / connected / error)
- FPS, latency
- detection mode, camera running state
- detection parameters (sliders)
- latest detection result
- logs (append-only terminal)

### Vision overlay
- Canvas or SVG overlay on camera feed
- Draw: bounding box, four corners (TL/TR/BR/BL), center point, angle arrow, pickup pose text
- Overlay coordinates map from backend `cornersPx` / `centerPx` / `angleDeg`

### Visual style
- Preserve `example_ui/real_time_detection_console_v2/code.html` dark cyber console
- Cyan primary `#4cd7f6`, emerald success, slate surfaces per `example_ui/precision_optic_interface/DESIGN.md`
- Side nav, top status bar, camera panel, parameter panel, telemetry panel
- Responsive at 1366×768 and desktop

### Backend stack
- FastAPI, OpenCV, NumPy
- Inference: TFLite Runtime (preferred, matches project) or ONNX Runtime fallback
- Wrap existing `block_detected.pipeline.detect_block` and camera modules

### API endpoints
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

### Pydantic schemas (backend)
- `DetectionParams`, `DetectionResult`, `CornerPoint`, `PickupPose`
- `ClassificationScores`, `SystemStatus`

### Frontend TypeScript contract (camelCase JSON wire format)
Must match backend output exactly:
- `blockId`, `confidence`, `centerPx`, `cornersPx`, `angleDeg`
- `pickupPoseMm`, `fps`, `latencyMs`, `valid`, `rejectReason`

Map from existing Python contract:
- `block_id` → `blockId`, `center_px` → `centerPx`, etc.
- `pickup_pose` → `pickupPoseMm` with `xMm`, `yMm`, `thetaDeg`
- `corners_px` → `cornersPx` with `tl`, `tr`, `br`, `bl` or array `[tl, tr, br, bl]`

### Integration layer
- `frontend/lib/api.ts` — REST client
- `frontend/lib/ws.ts` — WebSocket with auto-reconnect
- `frontend/types/vision.ts` — shared types

### Parameter UX
- Sliders update Zustand immediately
- Debounced POST to `/api/detection/params` (300–500ms)

### Mock mode
- Backend env `MOCK_CAMERA=true` or `DETECTION_MODE=mock`
- Stable fake detection data when no camera/model
- Clear `# TODO:` comments at mock injection points

### DevOps
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

</decisions>

<canonical_refs>
## Canonical References

**Downstream agents MUST read these before planning or implementing.**

### Detection contract (source of truth)
- `src/block_detected/detection_contract.py` — `DetectionResult`, `CornersPx`, `PickupPose`, statuses
- `detection_contract.py` — root shim

### Existing pipeline
- `src/block_detected/pipeline.py` — `detect_block`
- `src/block_detected/camera.py` — frame sources
- `config/vision.example.json` — tunable vision parameters
- `config/calibration.example.json` — calibration schema

### UI reference (do not delete)
- `example_ui/real_time_detection_console_v2/code.html` — primary layout reference
- `example_ui/precision_optic_interface/DESIGN.md` — design tokens

### Project constraints
- `CLAUDE.md` — stack, no ArUco, TFLite INT8, 640×480

</canonical_refs>

<specifics>
## Specific Ideas

- All buttons must call real backend endpoints or safe mock handlers — no dead buttons
- WebSocket shows live FPS/latency + latest `DetectionResult`
- MJPEG `<img src={STREAM_URL}>` or fetch stream in CameraViewport
- Classification panel shows 4-class scores when available
- Log terminal mirrors backend events + connection state changes
- Keep `example_ui/` untouched as visual reference

</specifics>

<deferred>
## Deferred Ideas

- OPS-01 live tuning beyond current slider set (v2)
- RUN-01 multi-block scene graph (v2)
- RUN-02 temporal filtering (v2)
- nginx TLS termination (production hardening, not v1 console)

</deferred>

---

*Phase: 09-next-js-fastapi-detection-console-ui-with-websocket-telemetr*
*Context gathered: 2026-05-31*

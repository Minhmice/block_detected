# Phase 11: Edge Impulse .eim Deployment — Context

**Gathered:** 2026-05-31
**Status:** Ready for planning
**Source:** User specification (`/gsd-add-phase`)

<domain>
## Phase Boundary

Deploy Edge Impulse Linux AARCH64 `.eim` model on Raspberry Pi 5 (64-bit) into the existing FastAPI + Next.js detection console. Load the model once at startup, run inference on camera frames, and stream normalized detection telemetry to the frontend.

**In scope:**
- Model placement at `backend/models/block_detector.eim` with env config and gitignore
- `edge_impulse_linux` runtime dependency + documented system packages
- Startup validation (model exists, executable, `chmod +x` guidance)
- `edge_impulse_runner.py` wrapper: single runner instance, BGR frames in, `DetectionResult` out
- Wire into `/health`, detection start/stop, MJPEG stream, WebSocket loop
- `VISION_MOCK_MODE=true` fallback with stable fake detections
- `make dev` / `npm run dev:all` orchestration + README section
- Validation on target arch (`uname -m`, `getconf LONG_BIT`, chmod, backend tests)

**Out of scope:**
- Retraining or re-exporting the Edge Impulse impulse (model already exported)
- Replacing OpenCV contour/geometry pipeline where still needed for corners/pose
- ArUco or alternate classifier backends

**Existing asset:**
- Exported model: `models/minhmice-project-1-linux-aarch64-v1-impulse-#2.eim` (copy to `backend/models/block_detector.eim`)

</domain>

<decisions>
## Implementation Decisions

### Model placement
- Directory: `backend/models/`
- Canonical path: `backend/models/block_detector.eim`
- `.gitignore`: `backend/models/*.eim`
- `.env.example` additions:
  - `EI_MODEL_PATH=backend/models/block_detector.eim`
  - `VISION_MOCK_MODE=false`

### Runtime dependency
- Python: `edge_impulse_linux`
- System (document in README):
  - `libatlas-base-dev libportaudio0 libportaudio2 libportaudiocpp0 portaudio19-dev`
- Startup checks:
  - Model file exists at `EI_MODEL_PATH`
  - Model is executable; if not, run or document `chmod +x backend/models/block_detector.eim`

### Inference wrapper (`backend/app/services/edge_impulse_runner.py`)
- Load model path from env once at init (not per frame)
- Expose `classify_frame(frame: np.ndarray) -> DetectionResult`
- Accept OpenCV BGR frames; resize/convert per Edge Impulse SDK requirements
- Map SDK output to project schema:
  - `blockId`, `confidence`, `centerPx`, `cornersPx`, `angleDeg`, `pickupPoseMm`
  - `fps`, `latencyMs`, `valid`, `rejectReason`

### Backend integration
Wire runner into existing FastAPI routes:
- `GET /health` — report model loaded / mock mode / errors
- `POST /api/detection/start` — start loop with EI runner
- `POST /api/detection/stop`
- `GET /video/stream` — MJPEG with optional overlay
- `WS /ws/detection` — live telemetry

Detection loop:
1. Read camera frame
2. Run OpenCV contour/perspective if still required for geometry
3. Pass crop or full frame to `.eim`
4. Send result over WebSocket
5. Stream MJPEG preview

### Mock fallback
- When `VISION_MOCK_MODE=true`, skip `.eim` entirely
- Return stable fake detections so frontend continues to work on dev machines without aarch64 EI runtime

### Dev orchestration
- Ensure one command starts FastAPI + Next.js: `make dev` or `npm run dev:all`
- README section: model placement, chmod, deps install, run backend, test `/health`, open frontend

</decisions>

<success_criteria>
## Success Criteria (planning input)

1. `backend/models/block_detector.eim` exists (or documented copy step from exported `.eim`) and is gitignored
2. Backend starts with model existence + executable checks; `/health` reports EI status
3. On Pi 5 aarch64 with `VISION_MOCK_MODE=false`, live camera frames produce WebSocket telemetry with mapped `DetectionResult` fields
4. On dev Mac/x86 with `VISION_MOCK_MODE=true`, console works without EI binary
5. `make dev` or `npm run dev:all` documented and working
6. Validation commands recorded: `uname -m`, `getconf LONG_BIT`, `chmod +x`, backend lint/test if available

</success_criteria>

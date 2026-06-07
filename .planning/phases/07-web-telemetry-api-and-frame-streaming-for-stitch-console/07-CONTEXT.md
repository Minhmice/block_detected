# Phase 7: Web telemetry API and frame streaming for Stitch console - Context

**Gathered:** 2026-06-07
**Status:** Ready for planning
**Mode:** Auto-generated (autonomous)

<domain>
## Phase Boundary

HTTP/WebSocket backend exposing `WebcamEngine` to Stitch `code.html`: MJPEG or WebSocket frame stream, START/STOP, NEXT CAMERA, NEXT MODEL, telemetry JSON (FPS, latency_ms, render_ms), log tail from `get_log_lines()`. New layer `runtime/api/` or `apps/web/` — no detection logic duplicated.

</domain>

<decisions>
## Implementation Decisions

### API Stack
- Use FastAPI + uvicorn (add to pyproject optional deps `[web]`)
- Single process: API server owns or wraps WebcamEngine instance
- MJPEG `/stream` endpoint for `<img src>` compatibility with code.html

### Telemetry Contract
- JSON shape matching html_data_requirements.md §2: fps, latency_ms, render_ms
- Aggregate latency = frame_read_ms + inference_ms (document mapping)
- Log tail: last N lines from get_log_lines()

### Engine Control
- POST /api/start, /api/stop, /api/camera/next, /api/model/next
- Wrap existing WebcamEngine methods — no reimplementation

### Architecture
- `runtime/api/` for routes + schemas; `apps/web/server.py` thin entry
- Dependency rule: api → runtime, not apps/gui

### Claude's Discretion
WebSocket vs MJPEG — prefer MJPEG first for simplicity; WS for telemetry optional second endpoint.

</decisions>

<code_context>
## Existing Code Insights

### Reusable Assets
- `runtime/engine.py` — WebcamEngine (process_frame, switch_camera, switch_model, shutdown)
- `runtime/metrics.py` — FPS, stage latencies
- `runtime/logging_setup.py` — get_log_lines()
- `core/domain.py` — InferenceStats, FrameResult
- `example_ui/stitch_block_pickup_vision_console/code.html` — target UI
- `example_ui/.../BACKEND_GAP_ANALYSIS.md` — gap spec

### Integration Points
- New entry: `python -m block_detected.web` or `block-detected-web` script
- CORS enabled for local dev (file:// or localhost)

</code_context>

<specifics>
Unblock Stitch UI shell — stream + metrics + log before sidebar params (Phase 8+).

</specifics>

<deferred>
Primary target kinematics — Phase 13
Classical pipeline overlays — Phase 12

</deferred>

---
status: testing
phase: 09-next-js-fastapi-detection-console-ui-with-websocket-telemetr
source: 09-01-SUMMARY.md, 09-02-SUMMARY.md
started: 2026-05-31T22:00:00Z
updated: 2026-05-31T22:00:00Z
---

## Current Test

number: 1
name: Cold Start Smoke Test
expected: |
  Kill any running backend/frontend processes. Copy `.env.example` → `.env` and `frontend/.env.local.example` → `frontend/.env.local` with `MOCK_CAMERA=true`. From repo root run `make dev` (or `npm run dev:all`). Backend listens on :8000, frontend on :3000. `GET /health` returns JSON with `mockCamera: true`. No startup crash in either terminal.
awaiting: user response

## Tests

### 1. Cold Start Smoke Test
expected: Kill processes, fresh env, `make dev` starts backend :8000 + frontend :3000; `/health` returns mockCamera true; no startup errors
result: [pending]

### 2. Console Home Loads
expected: Open http://localhost:3000 — dark cyber console with sidebar, top status bar (VISION_OS), camera panel shows live MJPEG feed from mock images
result: [pending]

### 3. Detection Telemetry Live
expected: With mock mode, TopStatusBar shows FPS > 0 and latency ms updating; classification panel shows block scores; VALID/INVALID badge updates
result: [pending]

### 4. Vision Overlay
expected: At 1366×768 width, overlay draws corner geometry on valid frames aligned with the block in the MJPEG feed (toggle chips work)
result: [pending]

### 5. Parameter Sliders Sync
expected: Move blurKernel or confidence slider — after ~400ms LogTerminal shows `API Params synced` with no ERR lines
result: [pending]

### 6. WebSocket Reconnect
expected: Stop backend process — TopStatusBar shows error/disconnected; restart backend — LogTerminal shows reconnect line and telemetry resumes
result: [pending]

### 7. REST Control Buttons
expected: RUN_DETECTION / STOP / Save Failed Frame / Quick Capture (datasets page) each succeed without dead buttons; LogTerminal logs API responses
result: [pending]

### 8. Secondary Routes
expected: `/calibration`, `/datasets`, `/system` load inside AppShell; system page shows health fields; calibration save and dataset capture call backend
result: [pending]

### 9. Layout Responsive
expected: At 1366×768, sidebar + 8/4 column grid with no horizontal scroll; camera min-height preserved
result: [pending]

## Summary

total: 9
passed: 0
issues: 0
pending: 9
skipped: 0
blocked: 0

## Gaps

[none yet]

---
phase: 07-web-telemetry-api-and-frame-streaming-for-stitch-console
plan: 03
subsystem: api
tags: [telemetry, logs, pytest, packaging, uvicorn]
requires:
  - plan: 07-01
    provides: schemas, EngineService
  - plan: 07-02
    provides: stream and control routes
provides:
  - GET /api/telemetry and /api/logs
  - Optional /ui static mount
  - [web] optional deps and block-detected-web script
  - tests/test_web_api.py (9 tests)
affects: [phase-8, stitch-console]
tech-stack:
  added: [fastapi>=0.115, uvicorn[standard]>=0.32, httpx>=0.27 dev]
  patterns: [TestClient with dependency_overrides, monkeypatch for bounded MJPEG test]
key-files:
  created:
    - src/block_detected/runtime/api/routes/telemetry.py
    - src/block_detected/apps/web/__main__.py
    - tests/test_web_api.py
  modified:
    - pyproject.toml
    - src/block_detected/apps/web/server.py
key-decisions:
  - "Stream test uses monkeypatched single-frame generator to avoid infinite-loop hang"
  - "is_running is a property, not a callable"
requirements-completed: [REQ-01, REQ-04]
duration: 25min
completed: 2026-06-07
---

# Phase 7 Plan 03: Telemetry, Logs, Tests, Packaging Summary

**Full Stitch toolbar/log API surface with 9 mocked TestClient tests and optional `[web]` install path.**

## Performance

- **Duration:** ~25 min
- **Tasks:** 3/3
- **Files modified:** 7
- **Tests:** 9 new (95 total suite)

## Task Commits

1. **Telemetry, logs, tests, packaging** - `5b952d0` (feat)

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 - Bug] Fixed is_running called as method in telemetry route**
- **Found during:** Task 1
- **Issue:** `service.is_running()` raised TypeError with MagicMock/bool property
- **Fix:** Changed to `service.is_running` property access
- **Files modified:** `runtime/api/routes/telemetry.py`

**2. [Rule 1 - Bug] Stream TestClient hung on infinite MJPEG generator**
- **Found during:** Task 3
- **Issue:** `test_stream_content_type` blocked on unbounded async generator
- **Fix:** Extracted `mjpeg_frames` to module level; test monkeypatches single-yield generator
- **Files modified:** `runtime/api/routes/stream.py`, `tests/test_web_api.py`

## Self-Check: PASSED

- `tests/test_web_api.py` — FOUND
- `python -m pytest tests/ -q` — 95 passed
- Commit `5b952d0` — FOUND

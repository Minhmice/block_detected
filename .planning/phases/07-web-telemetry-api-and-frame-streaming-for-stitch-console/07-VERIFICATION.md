# Phase 7 Verification

**Status:** passed  
**Date:** 2026-06-07

## Automated Checks

| Check | Result |
|-------|--------|
| `python -m pytest tests/test_web_api.py -q` | 9 passed |
| `python -m pytest tests/ -q` | 95 passed (no regressions) |
| EngineService import without camera | OK |
| `create_app()` registers all routes | OK |
| `[web]` extra + `block-detected-web` script in pyproject.toml | OK |

## Endpoints Implemented

| Method | Path | Purpose |
|--------|------|---------|
| GET | `/health` | Liveness probe |
| GET | `/stream` | MJPEG multipart/x-mixed-replace feed |
| POST | `/api/start` | Start engine frame loop |
| POST | `/api/stop` | Stop engine |
| POST | `/api/camera/next` | Cycle camera (409 if not running) |
| POST | `/api/model/next` | Cycle model (409 if not running) |
| GET | `/api/state` | Engine running state + model/camera |
| GET | `/api/telemetry` | FPS, latency_ms, render_ms JSON |
| GET | `/api/logs?limit=50` | Log tail from `get_log_lines()` |
| GET | `/ui/` | Static Stitch `code.html` (when example_ui dir exists) |

## How to Run Server

```bash
pip install -e ".[web]"
block-detected-web --host 127.0.0.1 --port 8765
# or
python -m block_detected.apps.web
```

Open `http://127.0.0.1:8765/ui/` for Stitch console (update `code.html` fetch/img URLs to this host).

## Test Coverage

- **File:** `tests/test_web_api.py`
- **Count:** 9 tests (mocked EngineService, no camera/weights)
- Tests: health, telemetry shape/idle, logs tail, start/stop control, stream content-type, camera-next guard, engine state

## Plans Completed

- [x] 07-01 — EngineService, schemas, FastAPI factory
- [x] 07-02 — MJPEG `/stream` + control routes
- [x] 07-03 — Telemetry/logs, packaging, tests

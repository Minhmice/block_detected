---
phase: 9
slug: next-js-fastapi-detection-console-ui-with-websocket-telemetr
status: draft
nyquist_compliant: false
wave_0_complete: false
created: 2026-05-31
---

# Phase 9 — Validation Strategy

> Per-phase validation contract for feedback sampling during execution.

---

## Test Infrastructure

| Property | Value |
|----------|-------|
| **Framework** | pytest 9.x (backend); Vitest (frontend, optional v1) |
| **Config file** | `pyproject.toml` `[tool.pytest.ini_options]` |
| **Quick run command** | `pytest tests/test_api_health.py -x` |
| **Full suite command** | `pytest tests/ -q` |
| **Estimated runtime** | ~30 seconds |

---

## Sampling Rate

- **After every task commit:** `pytest tests/test_api_*.py -x` (backend); `npm run lint --prefix frontend` (frontend)
- **After every plan wave:** `pytest tests/ -q` + existing pipeline tests
- **Before `/gsd-verify-work`:** Full pytest green; browser UAT for MJPEG + overlay + WS FPS
- **Max feedback latency:** 30 seconds

---

## Per-Task Verification Map

| Task ID | Plan | Wave | Requirement | Threat Ref | Secure Behavior | Test Type | Automated Command | File Exists | Status |
|---------|------|------|-------------|------------|-----------------|-----------|-------------------|-------------|--------|
| 09-01-01 | 01 | 0 | UI-09-08 | T-09-01 | Pydantic bounds on POST bodies | unit | `pytest tests/test_wire_schema.py::test_golden_detection_json -x` | ❌ W0 | ⬜ pending |
| 09-01-02 | 01 | 1 | UI-09-01 | — | N/A | integration | `pytest tests/test_api_health.py -x` | ❌ W0 | ⬜ pending |
| 09-03-01 | 03 | 2 | UI-09-05 | — | N/A | unit | `cd backend && python -c "from app.services.detection_loop import DetectionLoopService"` | ❌ W0 | ⬜ pending |
| 09-02-01 | 03 | 2 | UI-09-01 | — | N/A | integration | `pytest tests/test_api_stream.py::test_mjpeg_content_type -x` | ❌ W0 | ⬜ pending |
| 09-02-02 | 03 | 2 | UI-09-02 | — | N/A | integration | `pytest tests/test_api_ws.py::test_ws_telemetry_after_start -x` | ❌ W0 | ⬜ pending |
| 09-03-03 | 03 | 2 | UI-09-04 | T-09-02 | Path confinement on dataset save | integration | `grep -q is_relative_to backend/app/routes/dataset.py` | ❌ W0 | ⬜ pending |
| 09-04-02 | 04 | 3 | UI-09-07 | — | N/A | lint | `npm run lint --prefix frontend` | ❌ W0 | ⬜ pending |
| 09-05-02 | 05 | 4 | UI-09-03 | — | N/A | manual | overlay UAT at 1366×768 | ❌ W0 | ⬜ pending |
| 09-04-01 | 07 | 5 | UI-09-06 | T-09-02 | Path confinement on dataset save | smoke | `docker compose config -q` | ❌ W0 | ⬜ pending |
| — | — | — | CONT-01 | — | N/A | regression | `pytest tests/test_integration_pipeline.py -x` | ✅ | ⬜ pending |

*Status: ⬜ pending · ✅ green · ❌ red · ⚠️ flaky*

---

## Wave 0 Requirements

- [ ] `backend/requirements.txt` — FastAPI stack pins
- [ ] `tests/test_api_health.py` — `/health` JSON + camelCase
- [ ] `tests/test_api_stream.py` — MJPEG headers, reads first boundary
- [ ] `tests/test_api_ws.py` — WebSocket test client
- [ ] `tests/test_wire_schema.py` — golden camelCase fixture
- [ ] `tests/fixtures/wire/detection_success.json` — shared golden file
- [ ] Root `package.json` with `dev:all` script
- [ ] `Makefile` with `dev` target
- [ ] `.env.example` with all required variables

---

## Manual-Only Verifications

| Behavior | Requirement | Why Manual | Test Instructions |
|----------|-------------|------------|-------------------|
| Canvas overlay alignment | UI-09-04 | Letterboxing math needs visual QA | Open console at 1366×768; verify corners align with block in MJPEG |
| WebSocket reconnect UX | UI-09-07 | Browser timing | Kill backend; confirm UI shows error then reconnects |

---

## Validation Sign-Off

- [ ] All tasks have `<automated>` verify or Wave 0 dependencies
- [ ] Sampling continuity: no 3 consecutive tasks without automated verify
- [ ] Wave 0 covers all MISSING references
- [ ] No watch-mode flags
- [ ] Feedback latency < 30s
- [ ] `nyquist_compliant: true` set in frontmatter

**Approval:** pending

---
phase: 10
slug: real-camera-capture-on-dev-machine-no-mock-usb-pi-camera-liv
status: draft
nyquist_compliant: false
wave_0_complete: false
created: 2026-05-31
---

# Phase 10 — Validation Strategy

> Per-phase validation contract for feedback sampling during execution.

---

## Test Infrastructure

| Property | Value |
|----------|-------|
| **Framework** | pytest 9.x |
| **Config file** | `pyproject.toml` `[tool.pytest.ini_options]` |
| **Quick run command** | `PYTHONPATH=backend:src pytest tests/test_camera_source.py -x -q` |
| **Full suite command** | `PYTHONPATH=backend:src pytest tests/ -q` |
| **Estimated runtime** | ~15 seconds |

---

## Sampling Rate

- **After every task commit:** `PYTHONPATH=backend:src pytest tests/test_camera_source.py -x -q`
- **After every plan wave:** `PYTHONPATH=backend:src pytest tests/ -q`
- **Before `/gsd-verify-work`:** Full suite green + manual `camera_smoke.py --frames 3`
- **Max feedback latency:** 20 seconds

---

## Per-Task Verification Map

| Task ID | Plan | Wave | Requirement | Threat Ref | Secure Behavior | Test Type | Automated Command | File Exists | Status |
|---------|------|------|-------------|------------|-----------------|-----------|-------------------|-------------|--------|
| 10-01-01 | 01 | 0 | CAM-10-02 | — | N/A | unit | `pytest tests/test_camera_source.py::test_backend_selector_darwin -x` | ❌ W0 | ⬜ pending |
| 10-01-02 | 01 | 0 | CAM-10-02 | T-10-01 | ValueError on unknown cv_backend | unit | `pytest tests/test_camera_source.py::test_backend_selector_unknown_raises -x` | ❌ W0 | ⬜ pending |
| 10-01-03 | 01 | 0 | CAM-10-01 | — | N/A | unit | `pytest tests/test_camera_source.py::test_usb_capture_platform_backend -x` | ❌ W0 | ⬜ pending |
| 10-02-01 | 02 | 1 | CAM-10-01 | — | N/A | unit | `pytest tests/test_frame_source_factory.py::test_real_mode_uses_usb_profile -x` | ❌ W1 | ⬜ pending |
| 10-03-01 | 03 | 2 | CAM-10-03 | — | N/A | integration | `pytest tests/test_api_health.py::test_loop_idle_when_not_mock -x` | ❌ W2 | ⬜ pending |
| 10-03-02 | 03 | 2 | CAM-10-03 | — | N/A | integration | `pytest tests/test_api_detection.py::test_start_with_mocked_usb_source -x` | ❌ W2 | ⬜ pending |
| 10-04-01 | 04 | 3 | CAM-10-04 | — | N/A | manual | `python scripts/camera_smoke.py --config config/camera.usb.mac.json --frames 3` | ❌ W3 | ⬜ pending |

*Status: ⬜ pending · ✅ green · ❌ red · ⚠️ flaky*

---

## Wave 0 Requirements

- [ ] `tests/test_camera_source.py` — backend selector + mocked USB read (CAM-10-01, CAM-10-02)
- [ ] `src/block_detected/camera.py` — `_select_cv_backend`, `cv_backend` field

*Existing infrastructure covers mock factory and health baseline.*

---

## Manual-Only Verifications

| Behavior | Requirement | Why Manual | Test Instructions |
|----------|-------------|------------|-------------------|
| Live MJPEG in browser with real camera | CAM-10-03 | Requires macOS TCC camera permission + physical device | Set `.env` from `.env.real.example`, `make dev`, click INITIALIZE then RUN_DETECTION, confirm viewport shows live feed |
| camera_smoke on hardware | CAM-10-04 | TCC + hardware | `python scripts/camera_smoke.py --config config/camera.usb.mac.json --frames 3` prints 3 JSON frames with shape `[480,640,3]` |

---

## Validation Sign-Off

- [ ] All tasks have `<automated>` verify or Wave 0 dependencies
- [ ] Sampling continuity: no 3 consecutive tasks without automated verify
- [ ] Wave 0 covers all MISSING references
- [ ] No watch-mode flags
- [ ] Feedback latency < 20s
- [ ] `nyquist_compliant: true` set in frontmatter

**Approval:** pending

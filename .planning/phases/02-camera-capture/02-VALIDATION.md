---
phase: 02
slug: camera-capture
status: draft
nyquist_compliant: true
wave_0_complete: false
created: 2026-05-31
---

# Phase 02 - Validation Strategy

Per-phase validation contract for feedback sampling during execution.

## Test Infrastructure

| Property | Value |
|----------|-------|
| Framework | `pytest` for camera/debug modules; target-Pi smoke commands for hardware controls |
| Config file | none yet; Wave 0 creates dependency/config files |
| Quick run command | `python -m pytest tests/test_camera_source.py tests/test_debug_writer.py -q` |
| Full suite command | `python -m pytest -q` |
| Estimated runtime | ~20 seconds locally, excluding hardware smoke |

## Sampling Rate

- After every task commit: Run `python -m pytest tests/test_camera_source.py tests/test_debug_writer.py -q`
- After every plan wave: Run `python -m pytest -q`
- Before `/gsd-verify-work`: Full suite must be green and one target camera smoke must be recorded
- Max feedback latency: 30 seconds locally, manual hardware smoke excluded

## Per-Task Verification Map

| Task ID | Plan | Wave | Requirement | Threat Ref | Secure Behavior | Test Type | Automated Command | File Exists | Status |
|---------|------|------|-------------|------------|-----------------|-----------|-------------------|-------------|--------|
| 02-01-01 | 01 | 0 | CAM-01 | T-02-01 | fake/image source returns `(480, 640, 3)` BGR frames and monotonic `frame_id` | unit | `python -m pytest tests/test_camera_source.py::test_fake_source_returns_640x480_bgr -q` | no, W0 | pending |
| 02-01-02 | 01 | 1 | CAM-01 | T-02-01 | USB and Pi adapters fail clearly when backend cannot open or wrong shape is returned | unit/mocked | `python -m pytest tests/test_camera_source.py::test_backend_open_failure_is_explicit -q` | no, W0 | pending |
| 02-01-03 | 01 | 1 | CAM-02 | T-02-02 | settings metadata records requested, applied, verified, and unsupported exposure/WB controls | unit/mocked | `python -m pytest tests/test_camera_source.py::test_manual_control_metadata_records_support -q` | no, W0 | pending |
| 02-02-01 | 02 | 1 | CAM-03 | T-02-03 | debug writer saves raw and overlay artifacts using the same monotonic frame id | unit | `python -m pytest tests/test_debug_writer.py::test_debug_writer_uses_monotonic_frame_ids -q` | no, W0 | pending |
| 02-02-02 | 02 | 1 | CAM-03 | T-02-04 | debug output path is constrained and retention/sampling settings prevent unbounded writes | unit | `python -m pytest tests/test_debug_writer.py -q` | no, W0 | pending |

## Wave 0 Requirements

- [ ] `pyproject.toml` or `requirements-dev.txt` - pins local test dependencies for `pytest`, `numpy`, and `opencv-python`.
- [ ] `tests/test_camera_source.py` - covers CAM-01 and CAM-02 behavior with fakes/mocks.
- [ ] `tests/test_debug_writer.py` - covers CAM-03 filenames, write failures, and path/retention guards.
- [ ] `config/camera.example.json` - documents CSI/USB settings fields, manual controls, and debug options.
- [ ] `scripts/camera_smoke.py` or documented equivalent - records target Pi/USB smoke validation.

## Manual-Only Verifications

| Behavior | Requirement | Why Manual | Test Instructions |
|----------|-------------|------------|-------------------|
| Pi Camera CSI opens at 640x480 and records locked exposure/WB metadata | CAM-01, CAM-02 | local host lacks Pi Camera/libcamera hardware | On target Pi, run the smoke script with CSI backend and save stdout plus one raw debug frame. |
| USB camera controls lock exposure/WB when supported | CAM-01, CAM-02 | V4L2 support varies by camera/driver | On target Linux/Pi USB host, run the smoke script with USB backend and confirm unsupported controls are reported without crashing. |

## Validation Sign-Off

- [x] All tasks have automated verify or Wave 0 dependencies
- [x] Sampling continuity: no 3 consecutive tasks without automated verify
- [x] Wave 0 covers all missing references
- [x] No watch-mode flags
- [x] Feedback latency < 30s locally
- [x] `nyquist_compliant: true` set in frontmatter

**Approval:** approved 2026-05-31

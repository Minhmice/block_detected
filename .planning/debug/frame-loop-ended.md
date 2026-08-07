---
status: resolved
trigger: TUI shows "Frame loop ended (camera read failed or inference stopped)" with 0 latency
created: 2026-08-07
updated: 2026-08-07
---

## Symptoms

- TUI stops with generic "Frame loop ended" message
- Latency metrics drop to 0

## Root cause

1. `switch_camera()` used `open_v4l2()` (isOpened only) — could switch to camera that fails on `read()`
2. Single failed `cap.read()` immediately stopped entire TUI runtime
3. Generic error hid whether camera or inference failed

## Fix

- `switch_camera()` uses `try_open_index()` and skips current index
- Camera read retries (3 attempts) before failure
- `WebcamEngine.last_process_error` + specific TUI error message

## Verification

pytest test_tui_app, engine_create, camera_probe pass

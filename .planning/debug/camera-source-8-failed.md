---
status: resolved
trigger: Failed to open camera source 8 (640x480) in TUI on macOS
created: 2026-08-07
updated: 2026-08-07
---

## Symptoms

- **Expected:** TUI opens webcam and shows detections
- **Actual:** `Failed to open camera source 8 (640x480). Check permission`
- **Reproduction:** `python main.py --tui` on Mac

## Current Focus

hypothesis: Wrong camera index (8) + V4L2 backend unusable on macOS
next_action: fix defaults, config, and platform-aware camera backend

## Evidence

- `block_detected.json` had `camera.index: 8`; Mac only has cameras at index 0–1
- `defaults.py` and `schema.py` defaulted index to 8
- `open_v4l2` used `cv2.CAP_V4L2` — returns False on macOS even for index 0
- `cv2.VideoCapture(0, CAP_AVFOUNDATION)` works on this machine

## Resolution

root_cause: Stale default camera index 8 (no device) combined with Linux-only V4L2 backend on macOS desktop.
fix: Default index 0; schema uses defaults constants; platform-aware OpenCV backend (AVFoundation/DSHOW/V4L2); desktop auto-scan fallback; updated local JSON config
verification: pytest config tests pass; open_v4l2(0) and find_usb_camera succeed on Mac
files_changed: io/camera/v4l2.py, config/defaults.py, config/schema.py, runtime/session.py, block_detected.json

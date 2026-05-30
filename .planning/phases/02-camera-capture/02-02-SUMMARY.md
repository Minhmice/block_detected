---
phase: 02-camera-capture
plan: 02
subsystem: camera
tags: [picamera2, VideoCapture, CAM-02]
requirements-completed: [CAM-01, CAM-02]
completed: 2026-05-31
---

# Phase 02 Plan 02 Summary

**Hardware adapters: Picamera2 (CSI), USB OpenCV, `create_frame_source`, CAM-02 control metadata.**

## Accomplishments

- `PiCamera2FrameSource` with warmup + manual lock metadata (lazy picamera2 import)
- `UsbVideoCaptureFrameSource` with explicit open failures and V4L2 capture
- `scripts/camera_smoke.py` CLI for target Pi verification
- Mocked tests for USB open failure and Pi control metadata

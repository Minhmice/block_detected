# 10-01 Summary — Platform-aware USB backend

**Wave 0** | CAM-10-01, CAM-10-02

## Done

- Added `_select_cv_backend()` and `CameraSettings.cv_backend` in `camera.py`
- Replaced hardcoded `CAP_V4L2` in `UsbVideoCaptureFrameSource.start()`
- Extended `load_camera_settings()` for `cv_backend`
- Added 5 unit tests in `test_camera_source.py`

## Verify

`PYTHONPATH=backend:src pytest tests/test_camera_source.py -q` → 10 passed

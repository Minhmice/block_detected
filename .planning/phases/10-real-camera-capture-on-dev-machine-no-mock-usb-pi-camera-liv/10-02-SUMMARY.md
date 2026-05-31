# 10-02 Summary — Dev USB config and env

**Wave 1** | CAM-10-01, CAM-10-04

## Done

- `config/camera.usb.mac.json` — usb profile, `cv_backend: avfoundation`
- `.env.real.example` — MOCK_CAMERA=false template
- `.env.example` comment for real camera path
- `test_real_mode_uses_usb_profile` in `test_frame_source_factory.py`

## Verify

`PYTHONPATH=backend:src pytest tests/test_frame_source_factory.py -q` → 2 passed

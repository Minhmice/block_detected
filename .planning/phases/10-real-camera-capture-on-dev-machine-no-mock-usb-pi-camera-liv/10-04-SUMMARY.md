# 10-04 Summary — Docs and UAT

**Wave 3** | CAM-10-03, CAM-10-04

## Done

- README **Real camera on dev Mac** section (TCC, smoke, RUN_DETECTION)
- `scripts/camera_smoke.py` docstring example for `camera.usb.mac.json`
- `tests/conftest.py` — `hw_camera` marker
- `pyproject.toml` — pytest marker registration
- `10-UAT.md` — human verification checklist

## Verify

- `PYTHONPATH=backend:src pytest tests/ -q` green
- Manual: `camera_smoke.py --config config/camera.usb.mac.json --frames 3` (requires camera permission)

## Checkpoint

Human UAT Tests 1–3 pending operator run on dev Mac.

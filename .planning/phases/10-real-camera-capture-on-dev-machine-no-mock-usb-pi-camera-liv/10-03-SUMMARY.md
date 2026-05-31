# 10-03 Summary — Console real-camera path

**Wave 2** | CAM-10-03

## Done

- `test_loop_idle_when_not_mock` in `test_api_health.py`
- `tests/test_api_detection.py` — start with mocked USB source
- `detection_loop._run_loop` — `asyncio.to_thread` for `frame_source.start()`
- `TopStatusBar` — `LIVE_CAMERA` badge when not mock

## Verify

`PYTHONPATH=backend:src pytest tests/test_api_health.py tests/test_api_detection.py -q` → 3 passed

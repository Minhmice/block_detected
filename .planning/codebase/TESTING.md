# Testing Patterns

**Analysis Date:** 2026-06-02

## Test Framework

**Runner:** pytest `>=8.0` (dev optional dependency)

**Config:** `tests/conftest.py` inserts `src/` on `sys.path`

**Run:**
```bash
pip install -e ".[dev]"
python -m pytest tests/ -q
```

## Test Files

| File | Covers |
|------|--------|
| `test_geometry.py` | `vision.geometry.point_in_rect` |
| `test_boxes.py` | `parse_yolo_result`, `extract_boxes` with fakes |
| `test_config_paths.py` | `PROJECT_ROOT`, `MODELS_DIR` |
| `test_config_store.py` | load/save/validate TOML, defaults |
| `test_metrics.py` | `RuntimeMetrics.record` |
| `test_runtime_state.py` | overlay history deque |
| `test_engine.py` | `switch_model` success/failure (mocked `load_detector`) |

## Mocking Patterns

**YOLO result:** `_FakeResult` with `.boxes`, `.names` in `test_boxes.py`

**Detector:** `_FakeDetector` implementing predict/close in `test_engine.py`

**Config:** `tmp_path` TOML files in `test_config_store.py`

## What Is Not Tested

- Live webcam (`VideoCapture`)
- Real Ultralytics inference
- OpenCV window display
- End-to-end `main.py` GUI loop

## Coverage Gaps (acceptable for now)

- `vision/drawing/*` — visual; manual UAT via `python main.py`
- Full `WebcamEngine.process_frame` render path — needs OpenCV frame + YOLO mock at engine level

## Adding Tests

- Place new files as `tests/test_<module>.py`
- Keep imports from submodules (`block_detected.runtime.engine`) to avoid package `__init__` side effects

---

*Testing analysis: 2026-06-02*

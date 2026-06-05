# Testing Patterns

**Analysis Date:** 2026-06-05

## Test Framework

**Runner:**
- pytest ≥8.0 (declared in `pyproject.toml` under `[project.optional-dependencies] dev`)
- Config: `tests/conftest.py` only — no `pytest.ini`, `pyproject.toml [tool.pytest]`, or `setup.cfg` pytest section

**Assertion Library:**
- Plain `assert` statements (no `pytest.raises` usage detected in current suite)

**Run Commands:**
```bash
pip install -e ".[dev]"          # Install package + pytest
python -m pytest tests/ -q       # Run all tests (documented in README.md, AGENTS.md)
python -m pytest tests/test_postprocess.py -q   # Single module
python -m pytest tests/ -q --collect-only       # List tests without running
```

**Prerequisites:**
- Full suite requires main dependencies installed (`ultralytics`, `opencv-python`, `PySide6`) because importing `block_detected.runtime.engine` transitively imports `ultralytics` via `detection/yolo/loader.py`.
- A subset of tests (config, geometry, postprocess, boxes, log buffer, metrics, widgets) collects without engine imports when those modules are run in isolation; three engine-related files fail collection if `ultralytics` is missing.

## Test File Organization

**Location:**
- All tests live under `tests/` at repo root — not co-located with source.
- One test file per logical source area, prefixed with `test_`.

**Naming:**
- Files: `test_<area>.py` (e.g. `test_config_store.py`, `test_engine.py`, `test_gui_smoke.py`).
- Functions: `test_<behavior>_<condition>` (e.g. `test_switch_model_keeps_previous_detector_when_load_fails`, `test_filter_min_confidence_rejects_low_scores`).

**Structure:**
```
tests/
├── conftest.py              # sys.path bootstrap for src/
├── test_boxes.py            # detection/boxes.py
├── test_config_apply.py     # runtime/config_apply.py
├── test_config_paths.py     # config/paths.py
├── test_config_store.py     # runtime/config_store.py
├── test_engine.py           # runtime/engine.py (model switch)
├── test_engine_create.py    # runtime/engine.py (try_create/try_start)
├── test_geometry.py         # vision/geometry.py
├── test_gui_optional.py     # apps/gui import smoke
├── test_gui_smoke.py        # MainWindow offscreen (PySide6)
├── test_log_buffer.py       # runtime/logging_setup.py
├── test_metrics.py          # runtime/metrics.py
├── test_postprocess.py      # runtime/postprocess.py + vision/geometry.py
└── test_widgets.py          # vision/drawing/widgets.py
```

**Current scale:** 37 test functions across 13 files.

## Test Structure

**Suite Organization:**
- No test classes — all tests are module-level functions.
- Each test file opens with a module docstring describing scope and whether hardware is required.

Example from `tests/test_engine.py`:
```python
"""Tests for runtime engine behavior that does not require a real camera."""

from pathlib import Path

from block_detected.runtime.config_schema import AppConfig
from block_detected.runtime.engine import WebcamEngine


class _FakeDetector:
    ...


def test_switch_model_keeps_previous_detector_when_load_fails(monkeypatch):
    config = AppConfig.defaults()
    previous = _FakeDetector("old.pt")
    engine = WebcamEngine(config, [Path("old.pt"), Path("bad.pt")], previous)
    ...
    assert engine.detector is previous
```

**Patterns:**
- **Setup:** Build minimal state inline — `AppConfig.defaults()`, construct engine with injected fakes, no shared fixtures beyond pytest builtins.
- **Teardown:** Not used; tests avoid opening real cameras or loading real `.pt` weights.
- **Assertion:** Direct equality and length checks; substring checks on error messages for user-facing strings.

**Docstring convention in tests:**
- First line states isolation guarantees: `"Post-processing and temporal stability (no camera/model)."`, `"Engine create/start error messages without camera or weights."`

## Mocking

**Framework:** pytest `monkeypatch` fixture — `unittest.mock` is not used in the current suite.

**Patterns:**
```python
# Patch at the import path used by the module under test
monkeypatch.setattr("block_detected.runtime.engine.load_detector", fail_load)
monkeypatch.setattr("block_detected.runtime.engine.open_camera", lambda *_a, **_k: None)
monkeypatch.setattr(
    "block_detected.runtime.engine.discover_model_paths",
    lambda: [],
)
```

**Manual fakes instead of mocks:**
```python
class _FakeDetector:
    def __init__(self, name: str = "old.pt") -> None:
        self._name = name
        self.closed = False

    @property
    def model_name(self) -> str:
        return self._name

    def predict(self, frame, *, conf: float):
        raise AssertionError("not used")

    def close(self) -> None:
        self.closed = True
```

**YOLO result fakes** (`tests/test_boxes.py`):
```python
class _FakeTensor:
    def tolist(self):
        return self._values

    def item(self):
        return self._values[0] if isinstance(self._values, list) else self._values

class _FakeResult:
    def __init__(self, boxes):
        self.boxes = boxes
        self.names = {0: "block"}
```

**What to Mock:**
- External I/O: `load_detector`, `open_camera`, `discover_model_paths`.
- Optional GUI platform: set `QT_QPA_PLATFORM=offscreen` before constructing Qt widgets.

**What NOT to Mock:**
- Pure functions under test (`filter_min_confidence`, `iou`, `parse_yolo_result`, `validate_config`) — feed real inputs or lightweight fakes.
- Domain dataclasses and config objects — use `AppConfig.defaults()` and mutate fields as needed.
- NumPy arrays for drawing tests — use `np.zeros((h, w, 3), dtype=np.uint8)`.

## Fixtures and Factories

**Test Data:**
```python
# Factory helper at module level (tests/test_postprocess.py)
def _det(
    box: tuple[int, int, int, int],
    *,
    confidence: float = 0.9,
    class_id: int = 0,
    class_name: str = "block",
) -> Detection:
    return Detection(box=box, class_id=class_id, class_name=class_name, confidence=confidence)
```

**Built-in pytest fixtures used:**
- `tmp_path: Path` — TOML round-trip and invalid-config files (`tests/test_config_store.py`).
- `monkeypatch` — engine dependency substitution.

**Location:**
- No `tests/fixtures/` directory or shared `conftest.py` fixtures beyond path setup.
- Keep fake classes and `_det`-style helpers in the same file as the tests that use them.

**Config baseline:**
- Always start from `AppConfig.defaults()` unless testing explicit invalid values.

## Coverage

**Requirements:** None enforced — no coverage config or CI gate detected.

**View Coverage:**
```bash
# Not configured in repo; if adding coverage:
pip install pytest-cov
python -m pytest tests/ -q --cov=block_detected --cov-report=term-missing
```

## Test Types

**Unit Tests:**
- Primary test type — pure logic, config validation, metrics math, geometry, post-process filters, log buffer thread safety.
- No real webcam, no real YOLO weights, no GUI event loop in most tests.

**Integration Tests:**
- Limited — `test_gui_smoke.py` instantiates `MainWindow` with offscreen Qt platform when PySide6 is available.
- Engine tests integrate `WebcamEngine` with fake detectors but real engine code paths.

**E2E Tests:**
- Not used.

## Common Patterns

**Async Testing:**
- Not applicable — codebase is synchronous; GUI uses `QThread` but tests do not drive the thread loop except smoke instantiation.

**Error Testing:**
```python
engine, error = WebcamEngine.try_create(AppConfig.defaults())
assert engine is None
assert error is not None
assert ".pt" in error

ok, error = engine.try_start()
assert ok is False
assert "7" in error
```

**Validation error lists:**
```python
errors = validate_config(config)
assert any("default_conf" in e for e in errors)
assert any("camera.width" in error for error in errors)
```

**Optional dependency skip:**
```python
def test_mainwindow_instantiates_offscreen_when_pyside_available():
    pytest.importorskip("PySide6")
    os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
    ...
```

**Thread-safety test:**
```python
# tests/test_log_buffer.py — concurrent writer/reader threads
stop = threading.Event()
threads = [threading.Thread(target=writer), threading.Thread(target=reader)]
...
thread.join(timeout=2.0)
assert not thread.is_alive()
```

**Temporal/windowed logic:**
- Drive multi-step state explicitly with loops rather than mocking time (see `test_temporal_stability_requires_votes_across_window`).

**Timing/metrics:**
- Use synthetic `perf_counter`-style offsets (add small floats to `t0`) rather than sleeping:
```python
t0 = metrics.begin_frame()
stats = metrics.record(
    frame_start=t0,
    read_end=t0 + 0.01,
    infer_end=t0 + 0.03,
    render_end=t0 + 0.04,
    model_name="train-3.pt",
    camera_index=0,
)
assert stats.inference_ms > 0
assert stats.fps > 0
```

## Import Bootstrap

**conftest.py:**
```python
"""Pytest configuration — ensure src/ is importable without pip install -e ."""

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))
```

Prefer `pip install -e ".[dev]"` for development; conftest allows bare `pytest` from a checkout.

## Adding New Tests

**New pure function in `runtime/` or `vision/`:**
- Add assertions to an existing `tests/test_<module>.py` or create `tests/test_<new_module>.py`.
- Use `AppConfig.defaults()` and domain types from `block_detected.core.domain`.
- No monkeypatch unless calling code that hits I/O.

**New engine behavior:**
- Inject `_FakeDetector`; monkeypatch `load_detector`, `open_camera`, or `discover_model_paths` at `block_detected.runtime.engine.*` paths.
- Assert on return tuples and log-friendly error substrings, not raised exceptions.

**New GUI surface:**
- Add import smoke test in `tests/test_gui_optional.py` if only checking callability.
- For widget construction, follow `tests/test_gui_smoke.py`: `pytest.importorskip("PySide6")`, offscreen platform, instantiate, assert initial state, `window.close()`.

**New config fields:**
- Extend `tests/test_config_store.py` with validation and TOML round-trip cases.
- Add restart-key classification tests if the field requires camera/detector restart (`AppConfig.needs_camera_restart`).

## Gaps and Conventions to Preserve

**Untested or lightly tested areas (add tests when touching):**
- `detection/yolo/backend.py` — real Ultralytics load/infer (by design; use fakes at parse layer instead).
- `io/camera/capture.py` — no dedicated test file; patched only via engine tests.
- `ui/input/handlers.py` — no direct keyboard/mouse handler tests.
- Full `FrameThread` run loop and GUI save/restart flows.

**Do not:**
- Open real cameras or require `models/*.pt` in tests.
- Import `PySide6` at module top level in tests that should run headless — use `importorskip` inside the test or lazy import after skip.
- Read `LogBufferHandler._records` — test via `snapshot_lines()` / `get_log_lines()` only.

---

*Testing analysis: 2026-06-05*

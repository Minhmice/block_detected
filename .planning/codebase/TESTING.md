# Testing Patterns

**Analysis Date:** 2026-06-02

## Test Framework

**Runner:**
- Not detected — no test files, no `pytest.ini`, `pyproject.toml`, or `tox.ini`
- `.gitignore` includes `.pytest_cache/`, indicating pytest is anticipated but not set up

**Assertion Library:**
- Not applicable (no tests)

**Run Commands:**
```bash
# Not configured — no tests to run today
pytest                    # Would work after adding pytest to requirements and writing tests
python -m pytest          # Preferred invocation once pytest is added
python -m pytest -v       # Verbose
python -m pytest --cov=.  # Coverage (requires pytest-cov)
```

**Recommended setup for this project:**
```bash
pip install pytest pytest-cov
# Add to requirements-dev.txt or a [dev] extra:
# pytest>=8.0
# pytest-cov>=5.0
```

## Test File Organization

**Location:**
- No `tests/` directory exists
- Recommended: top-level `tests/` mirroring script names

**Naming:**
- Recommended pattern: `tests/test_main.py`, `tests/test_batch_detect_square.py`
- Use `test_<function_name>_<scenario>` for test functions: `test_clamp_bounds`, `test_discover_model_paths_empty_dir`

**Structure:**
```
block_detected/
├── main.py
├── batch_detect_square.py
├── tests/
│   ├── __init__.py          # optional; empty is fine
│   ├── conftest.py          # shared fixtures (mock YOLO, sample images)
│   ├── test_main.py
│   └── test_batch_detect_square.py
└── requirements.txt         # add pytest as dev dependency separately
```

## Test Structure

**Suite Organization:**
- Not present in codebase
- Recommended pattern once tests are added:

```python
# tests/test_batch_detect_square.py
from pathlib import Path

import pytest

from batch_detect_square import clamp, draw_square_box, parse_args


class TestClamp:
    def test_clamp_within_bounds(self):
        assert clamp(5, 0, 10) == 5

    def test_clamp_below_lo(self):
        assert clamp(-1, 0, 10) == 0

    def test_clamp_above_hi(self):
        assert clamp(99, 0, 10) == 10


def test_parse_args_defaults():
    args = parse_args()
    assert args.conf == 0.01
```

**Patterns:**
- **Setup:** Use `pytest` fixtures in `tests/conftest.py` for temp directories, fake model paths, and numpy/OpenCV test images
- **Teardown:** Prefer `tmp_path` fixture for filesystem tests; no manual cleanup needed
- **Assertion:** Plain `assert` statements (pytest style); no `unittest.TestCase` subclasses required

## Mocking

**Framework:**
- Not used; recommend `unittest.mock` (stdlib) or `pytest-mock` plugin

**Patterns:**
```python
from unittest.mock import MagicMock, patch

import numpy as np


def test_extract_boxes_empty_result():
    from main import extract_boxes

    result = MagicMock()
    result.boxes = None
    assert extract_boxes(result) == []


@patch("main.YOLO")
def test_main_exits_when_no_models(mock_yolo, tmp_path, monkeypatch):
    monkeypatch.setattr("main.MODELS_DIR", tmp_path / "models")
    (tmp_path / "models").mkdir()

    from main import main

    assert main() == 1
    mock_yolo.assert_not_called()
```

**What to Mock:**
- `ultralytics.YOLO` — avoid loading real `.pt` weights in unit tests
- `cv2.VideoCapture`, `cv2.imshow`, `cv2.waitKeyEx` — no hardware/display in CI
- `cv2.imread` / `cv2.imwrite` — control image I/O in batch tests
- Filesystem: use `tmp_path` instead of mocking `Path` when possible

**What NOT to Mock:**
- Pure helpers: `clamp()`, `point_in_rect()`, `extract_boxes()` (with constructed mock result objects)
- `discover_model_paths()` — test with real temp directories and `.pt` filenames (empty files suffice for discovery logic)
- `draw_square_box()` geometry — test with real `numpy` arrays from `np.zeros((100, 100, 3), dtype=np.uint8)`

## Fixtures and Factories

**Test Data:**
- Not present
- Recommended locations:
  - `tests/fixtures/` — small PNG/JPG samples (keep under ~50 KB)
  - `tests/conftest.py` — factory fixtures

**Example conftest:**
```python
# tests/conftest.py
import numpy as np
import pytest


@pytest.fixture
def blank_bgr_image():
    return np.zeros((480, 640, 3), dtype=np.uint8)


@pytest.fixture
def fake_yolo_result():
    """Minimal stand-in for ultralytics result with one box."""
    box = MagicMock()
    box.xyxy = [MagicMock(tolist=lambda: [10.0, 20.0, 50.0, 60.0])]
    box.cls = [MagicMock(item=lambda: 0)]
    box.conf = [MagicMock(item=lambda: 0.85)]

    result = MagicMock()
    result.boxes = [box]
    result.names = {0: "block"}
    return result
```

**Location:**
- `tests/conftest.py` for shared fixtures
- `tests/fixtures/` for binary test images (add to git if small; generate in fixture if not)

## Coverage

**Requirements:** None enforced

**View Coverage:**
```bash
pip install pytest-cov
python -m pytest --cov=main --cov=batch_detect_square --cov-report=term-missing
```

**Priority coverage targets (no GPU/display needed):**
| Module | Functions | Rationale |
|--------|-----------|-----------|
| `batch_detect_square.py` | `clamp`, `draw_square_box`, `parse_args` | Pure logic, easy unit tests |
| `main.py` | `discover_model_paths`, `default_model_index`, `extract_boxes`, `point_in_rect` | Pure logic |
| Both | `main()` early-exit paths | Validate error messages and exit codes with mocks |

**Low priority / integration-only:**
- Full webcam loop, live inference, `cv2.imshow` preview paths

## Test Types

**Unit Tests:**
- Primary approach for this codebase
- Scope: geometry helpers, path discovery, argument parsing, box extraction, label formatting
- Run quickly without model weights or camera

**Integration Tests:**
- Optional; run locally with a real small model in `models/` and sample images in `tests/fixtures/`
- Mark with `@pytest.mark.integration` and skip in CI by default:
```python
@pytest.mark.integration
def test_batch_end_to_end(tmp_path):
    ...
```
- Config in `pyproject.toml`:
```toml
[tool.pytest.ini_options]
markers = ["integration: needs model weights and opencv display"]
addopts = "-m 'not integration'"
```

**E2E Tests:**
- Not used
- Manual UAT only: run `python main.py` and `python batch_detect_square.py --show` per `README.md`

## CI/CD

**CI Pipeline:**
- Not detected — no `.github/workflows/`, GitLab CI, or similar

**Recommended minimal CI (when added):**
```yaml
# .github/workflows/test.yml
- run: pip install -r requirements.txt pytest pytest-cov
- run: python -m pytest -m "not integration" --cov=. --cov-fail-under=0
```

## Common Patterns

**Async Testing:**
- Not applicable — all code is synchronous

**Error Testing:**
```python
def test_main_missing_model(tmp_path, monkeypatch):
    monkeypatch.setattr("batch_detect_square.parse_args", lambda: argparse.Namespace(
        model=str(tmp_path / "missing.pt"),
        input=str(tmp_path),
        output=str(tmp_path / "out"),
        conf=0.01,
        show=False,
    ))
    (tmp_path / "img.png").write_bytes(b"")  # won't pass imread but model check runs first

    from batch_detect_square import main
    assert main() == 1
```

**Parametrize geometry edge cases:**
```python
@pytest.mark.parametrize("x1,y1,x2,y2,side", [
    (0, 0, 10, 20, 20),   # taller box → square side = height
    (0, 0, 30, 10, 30),   # wider box → square side = width
])
def test_draw_square_box_side(blank_bgr_image, x1, y1, x2, y2, side):
    from batch_detect_square import draw_square_box
    sx1, sy1, sx2, sy2 = draw_square_box(blank_bgr_image, x1, y1, x2, y2)
    assert sx2 - sx1 == side or sy2 - sy1 == side  # square dimensions
```

## Test Coverage Gaps

**Untested areas (entire codebase today):**

| Area | Files | Risk | Priority |
|------|-------|------|----------|
| Square box geometry / clamping | `batch_detect_square.py` | Wrong boxes on edge detections | High |
| Model path discovery | `main.py` | Webcam fails silently if discovery breaks | High |
| CLI defaults and overrides | `batch_detect_square.py` | Wrong paths/conf in production runs | Medium |
| Mouse callback / model switch | `main.py` | UI regression | Medium |
| Inference loops | Both scripts | Runtime errors on bad frames | Low (mock in unit tests) |
| Camera open/switch | `main.py` | Hardware-dependent | Low (mock only) |

## Manual Verification

**Documented in `README.md`:**
- Webcam: key bindings (`q`, `v`, `c`, arrows, `m`, `n`) and model button click
- Batch: default run, `--conf`, `--show`, output in `images_out/`

**Pre-release checklist:**
1. `python batch_detect_square.py` on `images/` — verify `images_out/` output
2. `python main.py` — verify model load, detection overlay, quit with `q`
3. Confirm `models/train-3.pt` exists locally (gitignored; not in CI without fixture model)

---

*Testing analysis: 2026-06-02*

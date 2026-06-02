# Testing Patterns

**Analysis Date:** 2026-06-02

## Test Framework

**Runner:**
- pytest `>=8.0` (optional dev dependency in `pyproject.toml` `[project.optional-dependencies] dev`)
- Config: **no** `pytest.ini` or `[tool.pytest.ini_options]` — defaults only

**Assertion Library:**
- Plain `assert` statements (stdlib)

**Run Commands:**
```bash
pip install -e ".[dev]"          # Install package + pytest
python -m pytest tests/ -q       # Run all tests (documented in README.md, AGENTS.md)
python -m pytest tests/ -v       # Verbose
python -m pytest tests/test_geometry.py -q   # Single file
```

## Test File Organization

**Location:**
- Separate `tests/` directory at repo root (not co-located with `src/`)

**Naming:**
- `test_<module_or_feature>.py`
- Test functions: `test_<behavior>_<condition>()` (e.g. `test_point_in_rect_inside`)

**Structure:**
```
tests/
├── conftest.py           # sys.path → src/
├── test_geometry.py      # vision.geometry
├── test_boxes.py         # detection.boxes (fakes)
├── test_config_paths.py  # config.paths
└── test_io_images.py     # io.images (tmp_path)
```

## Test Structure

**Suite Organization:**
```python
# tests/test_geometry.py — typical unit test
from block_detected.vision.geometry import point_in_rect


def test_point_in_rect_inside():
    assert point_in_rect(5, 5, (0, 0, 10, 10)) is True
```

**Patterns:**
- **Setup:** Minimal — no shared fixtures beyond `conftest.py` path hack
- **Teardown:** None required; `tmp_path` fixture auto-cleaned by pytest
- **Assertion:** Direct equality on primitives and lists

## Import / Path Setup

**conftest.py pattern:**
```python
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))
```

- Mirrors `main.py` bootstrap so tests run without `pip install -e .` (though editable install is recommended)
- Import as `from block_detected.<layer>...` not `from src.block_detected...`

## Mocking

**Framework:** None — manual fake classes instead of `unittest.mock`

**Patterns:**
```python
# tests/test_boxes.py — fake Ultralytics result structure
class _FakeTensor:
    def __init__(self, values):
        self._values = values
    def tolist(self):
        return self._values

class _FakeResult:
    def __init__(self, boxes):
        self.boxes = boxes
```

**What to Mock:**
- Ultralytics `Results` / tensor objects in `detection/boxes` tests
- Do not import `ultralytics` or `cv2` in unit tests unless testing integration (none today)

**What NOT to Mock:**
- Pure functions (`point_in_rect`) — test directly
- `config.paths` — assert real `PROJECT_ROOT` resolves to repo with `pyproject.toml`

## Fixtures and Factories

**Test Data:**
- `tmp_path` pytest builtin for filesystem tests (`test_io_images.py`)
- Write minimal bytes/files: `(tmp_path / "a.png").write_bytes(b"x")`

**Location:**
- Inline in test files; no `tests/fixtures/` directory

## Coverage

**Requirements:** None enforced — no coverage config or CI gate

**View Coverage:**
```bash
pip install pytest-cov   # not in pyproject.toml today
python -m pytest tests/ --cov=block_detected --cov-report=term-missing
```

## Test Types

**Unit Tests:**
- Scope: `core`, `config.paths`, `vision.geometry`, `detection.boxes`, `io.images`
- Approach: No GPU, no webcam, no model files required

**Integration Tests:**
- Not present — webcam loop (`apps/webcam/app.py`) untested automatically

**E2E Tests:**
- Not used — manual `python main.py` for full stack

## Common Patterns

**Filesystem tests:**
```python
def test_iter_image_paths_finds_png(tmp_path: Path):
    (tmp_path / "a.png").write_bytes(b"x")
    (tmp_path / "skip.txt").write_text("nope")
    paths = iter_image_paths(tmp_path)
    assert len(paths) == 1
```

**Config invariant tests:**
```python
def test_project_root_is_repo_root():
    assert (PROJECT_ROOT / "pyproject.toml").is_file()
```

**Async Testing:**
- Not applicable — synchronous code only

**Error Testing:**
- Not extensively used — e.g. empty `boxes` via `_FakeResult(None)` in `test_extract_boxes_empty`

## Adding Tests (Phase 3 guidance)

- Square-box drawing: pure OpenCV geometry tests without model — follow `test_geometry.py` style
- Batch app: prefer testing `iter_image_paths`, path helpers, and drawing functions in isolation before full YOLO integration
- If testing loader: use `tmp_path` with dummy `.pt` only if necessary; avoid committing weights

## Gaps vs AGENTS.md

- `AGENTS.md` lists example tests `test_geometry.py`, `test_boxes.py` — both exist
- Planned: square-box tests referenced in `.planning/ROADMAP.md` Phase 3 — not yet in `tests/`

---

*Testing analysis: 2026-06-02*

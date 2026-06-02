# Coding Conventions

**Analysis Date:** 2026-06-02

## Naming Patterns

**Files:**
- Use `snake_case.py` at project root for runnable scripts: `run_yolo_webcam.py`, `batch_detect_square.py`
- No package directory; scripts are standalone modules, not a `src/` layout

**Functions:**
- Use `snake_case` for all functions: `discover_model_paths()`, `extract_boxes()`, `draw_square_box()`, `parse_args()`
- Prefix helpers by action: `draw_*` for OpenCV rendering, `open_*` for resource acquisition, `parse_*` for CLI
- Entry point is always `main() -> int`

**Variables:**
- Use `snake_case` for locals and parameters: `model_paths`, `current_path`, `box_history`, `det_count`
- Use descriptive names for OpenCV geometry: `x1`, `y1`, `x2`, `y2`, `sx1`, `sy1`, `sx2`, `sy2`
- Loop indices: `idx` with `enumerate(..., start=1)` for user-facing progress output

**Constants:**
- Use `SCREAMING_SNAKE_CASE` at module top for configuration: `BASE_DIR`, `MODELS_DIR`, `DEFAULT_MODEL_NAME`, `CAMERA_INDEX`, `CONF_MIN`, `WINDOW_NAME`
- Group related constants together (camera settings, confidence bounds, UI layout) before function definitions
- Default model filename is a string constant (`DEFAULT_MODEL_NAME = "train-3.pt"`), not repeated inline

**Types:**
- Use modern Python 3.10+ type hints where present: `list[Path]`, `tuple[int, int, int, int]`, `cv2.VideoCapture | None`, `dict`
- Return `int` from `main()` for process exit codes (0 success, 1 failure)
- Type hints are more complete in `run_yolo_webcam.py` than in `batch_detect_square.py`; match the richer style when adding code

## Code Style

**Formatting:**
- No formatter config detected (no `pyproject.toml`, `ruff.toml`, `.flake8`, or `black` config)
- Observed style: 4-space indentation, no trailing complexity, ~100–125 lines per script
- `.gitignore` references `.ruff_cache/` and `.mypy_cache/` but neither tool is configured yet

**Linting:**
- Not configured
- When adding linting, prefer `ruff` (already anticipated in `.gitignore`) with rules aligned to existing patterns below

**Line length:**
- No enforced limit; long `cv2.putText(...)` and status strings are split across lines naturally

## Import Organization

**Order:**
1. Standard library (`sys`, `argparse`, `collections`, `pathlib`)
2. Blank line
3. Third-party (`cv2`, `ultralytics`)

**Example from `run_yolo_webcam.py`:**
```python
import sys
from collections import deque
from pathlib import Path

import cv2
from ultralytics import YOLO
```

**Path Aliases:**
- None; no package structure or import aliases
- Resolve paths relative to script location via `BASE_DIR = Path(__file__).resolve().parent`

## Module Layout

**Standard script structure:**
1. Imports
2. `BASE_DIR` and module-level constants
3. Pure helper functions (discovery, drawing, geometry)
4. `main() -> int` with validation, loop, cleanup
5. `if __name__ == "__main__": raise SystemExit(main())`

**Path handling:**
- Always use `pathlib.Path`, not raw strings, for filesystem paths after parsing
- Default paths built from `BASE_DIR`: `BASE_DIR / "models" / "train-3.pt"`, `BASE_DIR / "images"`
- Convert to `str` only when passing to OpenCV or Ultralytics APIs: `YOLO(str(model_path))`, `cv2.imread(str(image_path))`

**Configuration:**
- Webcam tunables live as top-of-file constants in `run_yolo_webcam.py` (resolution, camera index, confidence bounds)
- Batch tunables use `argparse` in `batch_detect_square.py` via `parse_args()`

## Error Handling

**Patterns:**
- Validate preconditions early in `main()`; print `[ERROR]` and `return 1` on failure
- Use `[WARN]` for recoverable issues (unreadable image, camera switch failure, frame read failure)
- Use `[INFO]` for normal operational messages and user actions
- Wrap model load and inference in `try/except Exception` in `run_yolo_webcam.py`; log and exit or break loop
- Use `finally` for resource cleanup (camera release, window destroy) in `run_yolo_webcam.py`

**Exit codes:**
```python
def main() -> int:
    if not model_paths:
        print(f"[ERROR] No .pt models found in: {MODELS_DIR}")
        return 1
    # ...
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
```

**CLI validation (`batch_detect_square.py`):**
- Check model file exists, input directory exists, and at least one image is present before loading the model
- Skip individual unreadable images with `[WARN]` and `continue`; do not abort the whole batch

**When adding new scripts:**
- Follow the same `[LEVEL] message` prefix convention
- Return `1` for user-fixable setup errors; return `0` on normal completion
- Prefer `try/finally` for any resource that must be released (camera, windows, file handles)

## Logging

**Framework:** `print()` to stdout/stderr — no `logging` module

**Patterns:**
- Prefix every message with a level tag in brackets: `[ERROR]`, `[WARN]`, `[INFO]`
- Include actionable context (paths, counts, model names) in the message
- Progress output for batch: `[{idx}/{len(image_paths)}] Saved: {name} | detections: {count}`

**When to log:**
- `[ERROR]`: missing model, invalid input folder, model load failure, no images found
- `[WARN]`: skipped file, camera frame failure, no alternate camera available
- `[INFO]`: startup config, mode toggles, user quit, cleanup confirmation

## Comments

**When to Comment:**
- Use docstrings sparingly; only one exists today on `draw_model_switch_button()` in `run_yolo_webcam.py`
- Prefer self-explanatory function names over inline comments
- README (`README.md`) holds user-facing usage docs (Vietnamese); code comments are not required to duplicate README

**Docstrings:**
- One-line docstrings for non-obvious return values:
```python
def draw_model_switch_button(frame, model_name: str) -> tuple[int, int, int, int]:
    """Draw clickable button; returns (x1, y1, x2, y2)."""
```

## Function Design

**Size:**
- Keep helpers small and single-purpose: `extract_boxes()`, `clamp()`, `point_in_rect()`, `discover_model_paths()`
- `main()` holds the event loop and orchestration; extract drawing and I/O helpers when logic exceeds ~15 lines

**Parameters:**
- Pass OpenCV frames and YOLO `result` objects directly; no wrapper classes
- Use optional state via `dict` for OpenCV mouse callbacks: `ui_state: dict = {"button_rect": None}`
- Nested closures with `nonlocal` for UI actions tied to loop state (`switch_model()` in `run_yolo_webcam.py`)

**Return Values:**
- Helpers return concrete data: `list[Path]`, box tuples, clamped coordinates, button rect
- `main()` returns process exit code only
- `parse_args() -> argparse.Namespace` in batch script

## YOLO / OpenCV Patterns

**Model loading:**
- `YOLO(str(path))` after path validation
- Webcam: auto-discover all `models/*.pt` via `discover_model_paths()`; batch: single path from `--model`

**Inference API (inconsistency to be aware of):**
- `run_yolo_webcam.py` calls `model(frame, conf=..., verbose=False)` (callable syntax)
- `batch_detect_square.py` calls `model.predict(source=img, conf=..., verbose=False)`
- Both access `results[0]` and iterate `result.boxes`; check `result.boxes is None` before looping

**Box extraction pattern:**
```python
for box in result.boxes:
    x1, y1, x2, y2 = box.xyxy[0].tolist()
    cls_id = int(box.cls[0].item())
    conf = float(box.conf[0].item())
```

**Drawing:**
- Normal mode: `result.plot()` for annotated frame (webcam)
- Custom overlays: `cv2.rectangle`, `cv2.putText` with `cv2.FONT_HERSHEY_SIMPLEX`, `cv2.LINE_AA`
- Batch uses square boxes via `draw_square_box()` centered on detection with `clamp()` to image bounds

## Module Design

**Exports:**
- No `__init__.py` or package exports; each script is self-contained
- Helpers are module-private by convention (no leading underscore, but not imported elsewhere)

**Barrel Files:**
- Not used

**Shared code:**
- Duplicated patterns exist (`BASE_DIR`, box iteration, label formatting) across both scripts
- When adding shared logic, introduce a small module (e.g. `detection_utils.py`) rather than copying helpers a third time

## Adding New Code

**New runnable script:**
- Place at project root as `snake_case.py`
- Follow import order, `BASE_DIR`, constants, helpers, `main()`, `SystemExit` guard
- Document CLI flags in `README.md` if user-facing

**New helper shared by webcam and batch:**
- Add `detection_utils.py` at project root (no `src/` package yet)
- Keep OpenCV drawing and YOLO result parsing there; scripts remain thin entry points

**New constants:**
- Add to top of the relevant script unless shared across scripts, then move to a shared module

---

*Convention analysis: 2026-06-02*

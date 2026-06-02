# Coding Conventions

**Analysis Date:** 2026-06-02

## Naming Patterns

**Files:** snake_case (`config_schema.py`, `yolo/backend.py`)

**Classes:** PascalCase (`WebcamEngine`, `YoloDetector`, `AppConfig`)

**Functions:** snake_case (`load_detector`, `parse_yolo_result`)

## Layer Rules

- `detection` must not import `apps`, `ui`, or `runtime`
- `vision` must not import `detection`
- `core` must not import OpenCV or Ultralytics
- `runtime` may import `detection`, `vision`, `io`, `core`
- `apps` stays thin — delegate to `runtime` and `ui`

## Configuration

- Single typed source: `AppConfig` in `runtime/config_schema.py`
- Paths only in `config/paths.py`
- Do not scatter magic numbers outside config modules / `AppConfig`

## Logging

- Use `logging.getLogger(__name__)` — not `print()` in new code
- `apps/webcam/app.py` and `runtime/engine.py` use loggers
- Levels: INFO for user actions, WARNING for recoverable, ERROR for fatal setup

## Types

- `Box` = `tuple[int,int,int,int]` in `core/types.py`
- Prefer `Detection`, `FrameResult` from `core/domain.py` for parser output

## Error Handling

- Setup failures: log and return non-zero from `main()`
- Runtime inference errors: log and exit loop
- `switch_model`: on load failure, keep previous detector (see `runtime/engine.py`)

## Tests

- `tests/conftest.py` adds `src/` to path
- Mock YOLO `Results` with fake box tensors (see `tests/test_boxes.py`)
- No webcam, no real `.pt` in unit tests

---

*Convention analysis: 2026-06-02*

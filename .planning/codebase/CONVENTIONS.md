# Coding Conventions

**Analysis Date:** 2026-06-05

## Naming Patterns

**Files:**
- Use `snake_case.py` for all Python modules (e.g. `config_schema.py`, `logging_setup.py`).
- Place tests in `tests/test_<module_or_area>.py` mirroring the source area (e.g. `tests/test_postprocess.py` for `runtime/postprocess.py`).
- Package entry points: `main.py` (repo root), `__main__.py` (package CLI), `app.py` (GUI).

**Functions:**
- Use `snake_case` for all functions and methods (e.g. `parse_yolo_result`, `apply_hot_config`, `filter_min_confidence`).
- Use the `try_<action>` / `<action>` pair when a soft-failure API is needed:
  - `try_create` returns `(WebcamEngine | None, str | None)`; `create` returns `WebcamEngine | None`.
  - `try_start` returns `(bool, str | None)`; `start` returns `bool`.
- Prefix private helpers with `_` (e.g. `_render`, `_toml_value`, `_frame_to_qimage`, `_detection_matches`).
- Use verb-first names for actions: `load_config`, `save_config`, `discover_model_paths`, `merge_duplicate_detections`.

**Variables:**
- Use `snake_case` for locals and instance attributes (e.g. `model_paths`, `frame_start`, `active_conf`).
- Prefix intentionally private instance fields with `_` (e.g. `_detector`, `_cap`, `_postprocess`, `_frame_times`).
- Use descriptive names for config sections bound to locals: `inf = self.config.inference`, `ui = self.config.ui`.

**Types and classes:**
- Use `PascalCase` for classes and dataclasses (e.g. `WebcamEngine`, `DetectionPostProcessor`, `AppConfig`).
- Use `PascalCase` for nested config dataclasses (e.g. `CameraConfig`, `StabilityConfig`, `RuntimeState`).
- Use `TypeAlias` for simple aliases in `core/types.py` (e.g. `Box: TypeAlias = tuple[int, int, int, int]`).
- Define protocols in `core/protocols.py` with `@runtime_checkable` and `Protocol` suffix omitted from name (e.g. `DetectorBackend`).

**Constants:**
- Use `SCREAMING_SNAKE_CASE` for module-level constants in `config/` (e.g. `DEFAULT_CONF`, `CONF_MIN`, `MODELS_DIR`, `RESTART_CAMERA_KEYS`).
- Group restart-key frozensets at module level in `runtime/config_schema.py` (e.g. `RESTART_CAMERA_KEYS`, `RESTART_DETECTOR_KEYS`).

**Test doubles:**
- Prefix fake/stub classes with `_Fake` inside test modules (e.g. `_FakeDetector`, `_FakeTensor`, `_FakeResult`).
- Prefix test-local factory helpers with `_` (e.g. `_det()` in `tests/test_postprocess.py`).

## Code Style

**Formatting:**
- No `.ruff.toml`, `setup.cfg`, `.flake8`, `mypy.ini`, or `.pre-commit-config.yaml` detected — rely on consistent manual style matching surrounding code.
- Use 4-space indentation throughout.
- Prefer trailing commas in multi-line dataclass/constructor calls when the call spans lines.
- Keep lines readable; break long import blocks and function signatures across lines when needed.

**Type hints:**
- Require type hints on public function signatures and class methods.
- Use `from __future__ import annotations` in modules that reference forward types (e.g. `runtime/engine.py`, `runtime/postprocess.py`, `apps/gui/app.py`).
- Use modern union syntax (`X | None`, `int | float`) — project requires Python ≥3.10 per `pyproject.toml`.
- Use `*` to mark keyword-only parameters where clarity matters (e.g. `predict(self, frame, *, conf: float)`, `filter_edge_boxes(..., *, frame_width: int, frame_height: int)`).
- Use `Any` sparingly for OpenCV frames and Ultralytics raw results where third-party types are impractical (e.g. `ProcessedFrame.annotated: Any`).

**Dataclasses:**
- Use `@dataclass(slots=True)` for mutable domain and runtime types (e.g. `FrameResult`, `RuntimeState`, `RuntimeMetrics`, `AppConfig` sections).
- Use `@dataclass(frozen=True, slots=True)` for immutable value objects (e.g. `Detection` in `core/domain.py`).
- Provide `@classmethod def defaults(cls) -> "AppConfig"` on root config types for canonical defaults.
- Use `field(default_factory=...)` for mutable defaults (e.g. `stats: InferenceStats = field(default_factory=InferenceStats)`).

**Linting:**
- Not detected. When adding tooling, align with existing patterns rather than mass-reformatting unrelated files.

## Import Organization

**Order:**
1. `from __future__ import annotations` (when used)
2. Standard library (`logging`, `pathlib`, `dataclasses`, `threading`, etc.)
3. Third-party (`cv2`, `numpy`, `ultralytics`, `PySide6` — lazy in GUI)
4. First-party absolute imports from `block_detected.*`

**Path style:**
- Always use absolute package imports: `from block_detected.runtime.engine import WebcamEngine`.
- Do not use relative imports (`from .engine import ...`) in application code.
- Patch targets in tests use the full module path string: `"block_detected.runtime.engine.load_detector"`.

**Layer boundaries (enforce in new code):**
- `core/` — no OpenCV, no YOLO, no PySide6.
- `detection/` — no `apps`, no `ui`, no `runtime`.
- `vision/` — no `detection` imports.
- `runtime/` — may use `detection`, `vision`, `io`, `core`; not `apps` or `ui`.
- `apps/` — thin orchestration; delegate to `runtime` + `ui`.

**Optional dependencies:**
- Wrap PySide6 imports in `try/except ModuleNotFoundError` in `apps/gui/app.py`; set placeholders to `None` and gate Qt class definitions behind `if QtCore is not None:`.
- Keep heavy imports out of `detection/yolo/__init__.py` re-exports — note that importing `block_detected.runtime.engine` transitively loads `ultralytics`.

**Barrel files:**
- Limited use. `detection/yolo/__init__.py` re-exports loader symbols with explicit `__all__`.
- Most modules are imported directly by path; do not add barrel files unless consolidating a stable public API.

## Error Handling

**Patterns:**
- Prefer `(result, error_message)` tuples for recoverable setup failures instead of raising to callers:
  - `WebcamEngine.try_create()` → `(engine | None, str | None)`
  - `WebcamEngine.try_start()` → `(bool, str | None)`
- Provide convenience wrappers that discard errors: `create()`, `start()` return only the success value.
- Log errors at point of failure with `logger.error(message)` before returning failure tuples (see `runtime/engine.py`).
- Return `None` from `process_frame()` on non-recoverable frame-loop failures (read failure, inference exception) after logging.
- Swallow non-fatal cleanup errors with `logger.warning` (e.g. `previous_detector.close()` in `switch_model`).

**Validation:**
- Collect validation errors as `list[str]` with dotted field paths — do not raise on first error:
  - `AppConfig.validate()` → `list[str]`
  - `validate_config(config)` in `runtime/config_store.py` delegates to `config.validate()`.
- Message format: `"{path} must be a number"` (e.g. `"inference.default_conf must be a number"`).

**Exceptions:**
- Use bare `except Exception as exc` only at I/O boundaries (model load, inference, detector close) where the caller should continue or return a soft failure.
- Do not catch exceptions silently without logging.
- Tests assert on error message content when verifying user-facing failures (e.g. `"7" in error`, `"models" in error.lower()`).

## Logging

**Framework:** Standard library `logging` via `runtime/logging_setup.py`.

**Setup:**
- Call `setup_logging(level: str)` once at app startup; it configures root logger, stdout stream handler, and ring-buffer handler.
- Set third-party noise down explicitly: `logging.getLogger("ultralytics").setLevel(logging.WARNING)`.

**Patterns:**
- Define module logger: `logger = logging.getLogger(__name__)` at module top (e.g. `runtime/engine.py`, `ui/input/handlers.py`, `apps/gui/app.py`).
- Use `%`-style formatting in log calls: `logger.info("Opened webcam source: %s", index)`.
- Log level comes from config: `AppConfig.ui.log_level` (string, e.g. `"INFO"`).
- GUI reads logs only through `get_log_lines()` — never access `LogBufferHandler._records` from UI code.

**Buffer handler:**
- `LogBufferHandler.snapshot_lines()` returns a defensive copy under a lock.
- Capacity default: 500 lines (`logging_setup.py`).

## Comments

**When to Comment:**
- Every module starts with a one-line docstring describing purpose (e.g. `"""Webcam runtime engine — frame loop, inference, render, metrics."""`).
- Document non-obvious protocols and placeholders (e.g. `ClassicalPipelineConfig` placeholder in `config_schema.py`).
- Explain threading/concurrency constraints in GUI worker code when behavior is non-obvious (see `AGENTS.md` for worker shutdown rules).

**Docstrings:**
- Use triple-quoted docstrings on public classes and non-trivial functions (e.g. `handle_key`, `switch_camera`, `TemporalStabilityTracker`).
- Keep docstrings brief — one sentence for simple helpers; include return semantics when not obvious (`handle_key` → `Returns True to continue the loop, False to quit`).
- Do not add docstrings to every private one-liner; code should be self-explanatory.

## Function Design

**Size:**
- Keep functions focused on one stage of the pipeline. Extract pure filters (e.g. `filter_min_confidence`, `merge_duplicate_detections`) rather than embedding logic in the engine loop.
- Engine methods orchestrate; vision/detection/runtime helpers implement.

**Parameters:**
- Pass config slices explicitly to functions that need them (`handle_key(..., inference: InferenceConfig, ui: UiDebugConfig)`).
- Pass frame dimensions as keyword args to post-processors: `processor.process(detections, frame_width=640, frame_height=480)`.
- Callback injection in UI handlers: `switch_model` passed as callable rather than importing engine in `ui/input/handlers.py`.

**Return Values:**
- Pure functions return new lists rather than mutating inputs (all filters in `runtime/postprocess.py` return `list[Detection]`).
- Geometry helpers return primitives (`float` for `iou`, `int` for `box_area`, `bool` for `point_in_rect`).
- Domain parsing returns `FrameResult` wrapping `list[Detection]` plus optional `raw` payload.

## Module Design

**Exports:**
- No wildcard exports. Explicit imports at call sites.
- `__all__` only where a subpackage exposes a small stable API (`detection/yolo/__init__.py`).

**Configuration:**
- Defaults live in `AppConfig.defaults()` / nested dataclass field defaults — mirror legacy constants in `config/` modules.
- TOML persistence via `runtime/config_store.py`; hot-reload keys vs restart keys classified in `runtime/config_schema.py`.
- Path constants centralized in `config/paths.py` (`PROJECT_ROOT`, `MODELS_DIR`).

**Protocols and backends:**
- Define backend interface as `Protocol` in `core/protocols.py`.
- Concrete implementation in `detection/yolo/backend.py` (`YoloDetector`).
- Load through indirection: `runtime/detector_loader.load_detector(path) -> DetectorBackend`.

**GUI conventions:**
- `MainWindow` owns config UI; `FrameThread` (QThread) owns engine lifecycle.
- Pass `destroy_cv_windows=False` from GUI worker on shutdown — never call `cv2.destroyAllWindows()` from GUI code.
- Use run-generation guards so stale Qt signals do not update UI after stop.

**Testing-friendly extraction:**
- Extract hot-config logic to `runtime/config_apply.py` with comment `# testable helper`.
- Keep parse logic pure in `detection/boxes.py` so tests can feed fake result objects without loading YOLO.

---

*Convention analysis: 2026-06-05*

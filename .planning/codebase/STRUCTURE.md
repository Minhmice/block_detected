# Codebase Structure

**Analysis Date:** 2025-06-05

## Directory Layout

```
block_detected/                          # Repo root
├── main.py                              # Dev entry: sys.path bootstrap → GUI main
├── pyproject.toml                       # Package metadata, deps, console script
├── AGENTS.md                            # Layer rules and change map for agents
├── models/                              # YOLO .pt weights (gitignored contents; .gitkeep only)
├── block_detected.toml                  # Optional runtime config (not committed by default)
├── src/
│   └── block_detected/                  # Installable Python package
│       ├── __init__.py                  # __version__
│       ├── __main__.py                  # python -m block_detected
│       ├── apps/
│       │   └── gui/
│       │       ├── __init__.py
│       │       └── app.py               # PySide6 MainWindow, FrameThread, main()
│       ├── runtime/
│       │   ├── engine.py                # WebcamEngine
│       │   ├── state.py                 # RuntimeState
│       │   ├── metrics.py               # RuntimeMetrics
│       │   ├── postprocess.py           # DetectionPostProcessor
│       │   ├── config_schema.py         # AppConfig dataclasses
│       │   ├── config_store.py          # TOML load/save
│       │   ├── config_apply.py          # Hot-reload helpers
│       │   ├── detector_loader.py       # load_detector()
│       │   └── logging_setup.py         # setup_logging, get_log_lines
│       ├── core/
│       │   ├── types.py                 # Box type alias
│       │   ├── domain.py                # Detection, FrameResult, stats types
│       │   └── protocols.py             # DetectorBackend Protocol
│       ├── detection/
│       │   ├── boxes.py                 # parse_yolo_result
│       │   └── yolo/
│       │       ├── loader.py            # discover_model_paths
│       │       └── backend.py           # YoloDetector
│       ├── vision/
│       │   ├── geometry.py              # IoU, box_area, point_in_rect
│       │   └── drawing/
│       │       ├── detections.py        # draw_detection_boxes
│       │       ├── eval.py              # draw_eval_boxes (raw YOLO result)
│       │       └── widgets.py           # status bar, model button
│       ├── io/
│       │   └── camera/
│       │       └── capture.py           # open_camera, switch_camera
│       ├── ui/
│       │   └── input/
│       │       └── handlers.py          # OpenCV key/mouse handlers
│       └── config/
│           ├── paths.py                 # PROJECT_ROOT, MODELS_DIR
│           ├── camera.py                # Legacy camera constants
│           ├── inference.py             # Confidence/model defaults
│           └── ui.py                    # Window/button/key constants
├── tests/                               # pytest suite (mirrors runtime/core/vision)
├── example_ui/                          # Stitch HTML mockups (design reference only)
├── .planning/                           # GSD phase artifacts and codebase docs
└── graphify-out/                        # Generated knowledge graph (do not hand-edit)
```

## Directory Purposes

**`src/block_detected/apps/`:**
- Purpose: Thin application shell
- Contains: GUI only (`gui/app.py`)
- Key files: `apps/gui/app.py`

**`src/block_detected/runtime/`:**
- Purpose: Engine, config, metrics, logging, post-processing orchestration
- Contains: All session lifecycle and pipeline wiring
- Key files: `engine.py`, `config_schema.py`, `config_store.py`, `postprocess.py`

**`src/block_detected/core/`:**
- Purpose: Domain types and detector protocol (stdlib-only)
- Contains: Dataclasses and `Protocol` definitions
- Key files: `domain.py`, `protocols.py`, `types.py`

**`src/block_detected/detection/`:**
- Purpose: ML backend and result parsing
- Contains: YOLO-specific code under `yolo/`, shared parsing in `boxes.py`
- Key files: `yolo/backend.py`, `yolo/loader.py`, `boxes.py`

**`src/block_detected/vision/`:**
- Purpose: Geometry and OpenCV overlay drawing
- Contains: Pure helpers + `drawing/` subpackage
- Key files: `geometry.py`, `drawing/detections.py`, `drawing/widgets.py`

**`src/block_detected/io/camera/`:**
- Purpose: Webcam capture abstraction
- Contains: OpenCV `VideoCapture` helpers
- Key files: `capture.py`

**`src/block_detected/ui/input/`:**
- Purpose: OpenCV-window input (legacy; GUI uses Qt)
- Contains: Keyboard/mouse callback functions
- Key files: `handlers.py`

**`src/block_detected/config/`:**
- Purpose: Filesystem paths and legacy module-level defaults
- Contains: Constants re-used by `AppConfig` defaults
- Key files: `paths.py`, `inference.py`, `camera.py`, `ui.py`

**`models/`:**
- Purpose: Local YOLO weight files (`*.pt`)
- Generated: No (user-supplied)
- Committed: `.gitkeep` only; weights typically gitignored

**`tests/`:**
- Purpose: Unit tests for runtime, config, geometry, postprocess, GUI smoke
- Contains: `test_*.py`, shared `conftest.py`
- Key files: `test_engine.py`, `test_postprocess.py`, `test_gui_smoke.py`

**`example_ui/`:**
- Purpose: External Stitch design exports (HTML/CSS mockups)
- Generated: Yes (design tooling)
- Committed: Reference only; not imported by application code

## Key File Locations

**Entry Points:**
- `main.py`: Local dev launcher with `src/` path injection
- `src/block_detected/__main__.py`: Module execution entry
- `src/block_detected/apps/gui/app.py`: `main()` — primary application entry
- `pyproject.toml` → `[project.scripts]` `block-detected`: Installed console command

**Configuration:**
- `src/block_detected/runtime/config_schema.py`: `AppConfig` and nested dataclasses, validation, restart key sets
- `src/block_detected/runtime/config_store.py`: TOML load/save; default path `block_detected.toml` at repo root
- `src/block_detected/config/paths.py`: `PROJECT_ROOT`, `MODELS_DIR` resolution
- `block_detected.toml`: Optional user config file at repo root (create manually or via GUI save)

**Core Logic:**
- `src/block_detected/runtime/engine.py`: Frame loop orchestration
- `src/block_detected/runtime/postprocess.py`: Stability and spatial filters
- `src/block_detected/detection/yolo/backend.py`: Ultralytics inference
- `src/block_detected/detection/boxes.py`: YOLO → domain type conversion

**GUI:**
- `src/block_detected/apps/gui/app.py`: `MainWindow`, `FrameThread`, controls, preview, log panel

**Testing:**
- `tests/conftest.py`: Shared pytest fixtures
- `tests/test_engine.py`, `tests/test_postprocess.py`: Pipeline unit tests
- `tests/test_gui_smoke.py`, `tests/test_gui_optional.py`: GUI import/launch guards

## Naming Conventions

**Files:**
- Module names: `snake_case.py` (e.g. `config_schema.py`, `logging_setup.py`)
- One primary class or concern per file in `runtime/` and `detection/`
- Package `__init__.py` files re-export public symbols where present

**Directories:**
- Layer names match architectural role: `core`, `runtime`, `detection`, `vision`, `io`, `apps`, `ui`, `config`
- Nested by concern: `detection/yolo/`, `io/camera/`, `vision/drawing/`, `ui/input/`, `apps/gui/`

**Functions:**
- `snake_case`: `process_frame`, `load_config`, `parse_yolo_result`, `apply_hot_runtime_settings`
- Factory/class methods: `try_create`, `try_start` for error-tuple patterns

**Classes:**
- `PascalCase`: `WebcamEngine`, `YoloDetector`, `AppConfig`, `DetectionPostProcessor`, `MainWindow`, `FrameThread`
- Dataclasses for config and domain: `@dataclass` with `slots=True` where used in hot paths

**Types:**
- `PascalCase` dataclasses: `Detection`, `FrameResult`, `RuntimeStatus`
- Type alias: `Box = tuple[int, int, int, int]` in `core/types.py`
- Protocol: `DetectorBackend` in `core/protocols.py`

**Constants:**
- `SCREAMING_SNAKE_CASE` in legacy `config/` modules: `DEFAULT_CONF`, `MODELS_DIR`, `BUTTON_HEIGHT`
- Restart key frozensets in `config_schema.py`: `RESTART_CAMERA_KEYS`, `RESTART_DETECTOR_KEYS`

**Config TOML sections:**
- Lowercase section headers matching dataclass fields: `[camera]`, `[inference]`, `[stability]`, `[ui]`, `[classical]`

## Where to Add New Code

**New GUI control or panel widget:**
- Primary code: `src/block_detected/apps/gui/app.py` (`MainWindow._build_controls`, event wiring)
- Do not add YOLO or camera calls in GUI — queue requests to `FrameThread` / `WebcamEngine`

**New frame pipeline stage (e.g. classical CV):**
- Stage logic: new module under `vision/` or dedicated subpackage (keep `vision` free of `detection` imports)
- Orchestration hook: `src/block_detected/runtime/engine.py` in `process_frame()` or `_render()`
- Config: add fields to `ClassicalPipelineConfig` in `runtime/config_schema.py`

**New detector backend:**
- Implementation: `src/block_detected/detection/<backend>/backend.py` implementing `DetectorBackend`
- Wiring: `src/block_detected/runtime/detector_loader.py`
- Parsing: `src/block_detected/detection/boxes.py` or backend-specific parser returning `FrameResult`

**New post-inference filter or stability rule:**
- Filter function: `src/block_detected/runtime/postprocess.py`
- Geometry helper (if pure): `src/block_detected/vision/geometry.py`
- Config knobs: `StabilityConfig` in `runtime/config_schema.py`

**New domain type:**
- Add to: `src/block_detected/core/domain.py` or `core/types.py`
- Re-export from: `src/block_detected/core/__init__.py` if public

**New drawing overlay:**
- Implementation: `src/block_detected/vision/drawing/<name>.py`
- Import from: `vision/drawing/__init__.py` if part of public drawing API

**New camera or IO source:**
- Implementation: `src/block_detected/io/<source>/`
- Engine integration: `runtime/engine.py` start/read paths

**New config field:**
- Schema: `runtime/config_schema.py` (dataclass + `validate()` + `from_dict` field filter)
- Persistence: automatic via `to_dict()` / TOML if field is on an existing section
- Hot vs restart: add to `RESTART_*_KEYS` or handle in `runtime/config_apply.py` → `config_changed_keys()`

**New keyboard shortcut (OpenCV window mode):**
- Handler: `src/block_detected/ui/input/handlers.py`
- Key constant: `src/block_detected/config/ui.py`

**Tests:**
- Location: `tests/test_<module>.py` matching the layer under test
- Run: `python -m pytest tests/ -q` from repo root

**Utilities:**
- Pure geometry: `src/block_detected/vision/geometry.py`
- Path resolution: `src/block_detected/config/paths.py`
- Shared non-domain helpers: prefer colocating in the layer that owns the behavior; avoid a catch-all `utils/` unless one emerges

## Special Directories

**`.planning/`:**
- Purpose: GSD roadmap, phase plans, verification reports, codebase analysis docs
- Generated: Partially (agent-written during GSD workflows)
- Committed: Yes; refresh codebase docs via `/gsd-map-codebase` only

**`graphify-out/`:**
- Purpose: Knowledge graph output (`GRAPH_REPORT.md`, cache JSON)
- Generated: Yes (`graphify` tooling)
- Committed: Varies; do not use as source of truth for code changes

**`models/`:**
- Purpose: Ultralytics `.pt` weight files consumed by `discover_model_paths()`
- Generated: No (user/training pipeline supplies)
- Committed: Weights not committed; directory kept via `.gitkeep`

**`example_ui/`:**
- Purpose: Stitch block-pickup vision console HTML/CSS design reference
- Generated: Yes (design export)
- Committed: Reference mockups; no runtime import from `src/block_detected`

---

*Structure analysis: 2025-06-05*

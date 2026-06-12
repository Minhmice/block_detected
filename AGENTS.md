# Agent guide — CV package layout

Read this before editing. The package uses **layered folders** plus a **runtime** layer for engine/config/metrics (GUI-ready).

## Layer diagram

```
apps/          thin orchestration (GUI entry)
runtime/       engine, typed config (TOML), metrics, logging, detector loader
config/        legacy path constants + module defaults (re-export targets)
core/          domain types + protocols — no OpenCV/YOLO
detection/     detector backends + result parsing
  └── yolo/    Ultralytics YOLO (.pt weights)
vision/        draw/geometry on frames — no detection imports
io/            cameras, files, streams
  └── camera/
ui/            keyboard/mouse callbacks
  └── input/
```

**Dependency rules:**
- `detection` → no `apps`, no `ui`, no `runtime`
- `vision` → no `detection`
- `core` → no OpenCV/YOLO
- `runtime` → may use `detection`, `vision`, `io`, `core` (not `apps`, not `ui`)
- `apps` → thin; delegates to `runtime` + `ui`

## Directory tree

```
src/block_detected/
├── apps/gui/
│   ├── app.py                  # PySide6 entry (main.py --gui)
│   ├── robo_window.py          # Composes widgets; runtime wiring
│   ├── theme.py                # COLORS + modular QSS from DESIGN.md
│   ├── widgets/                # HeaderBar, PipelineSidebar, cards, etc.
│   └── worker.py               # FrameThread (Qt worker)
├── runtime/
│   ├── engine.py               # WebcamEngine — read/infer/render/metrics
│   ├── state.py                # RuntimeState (conf, eval)
│   ├── metrics.py              # FPS + stage latencies
│   ├── config_schema.py        # AppConfig dataclasses + validate + hot/restart keys
│   ├── config_store.py         # load/save TOML (block_detected.toml)
│   ├── detector_loader.py      # load_detector(path) → YoloDetector
│   ├── postprocess.py          # stability filters + temporal votes
│   └── logging_setup.py        # logging + ring buffer for GUI log panel
├── config/
│   ├── paths.py                # PROJECT_ROOT, MODELS_DIR
│   ├── camera.py               # legacy constants (defaults mirror AppConfig)
│   ├── inference.py
│   └── ui.py
├── core/
│   ├── types.py                # Box
│   ├── domain.py               # Detection, FrameResult, InferenceStats, RuntimeStatus
│   └── protocols.py            # DetectorBackend Protocol
├── detection/
│   ├── boxes.py                # parse_yolo_result, extract_boxes
│   └── yolo/
│       ├── loader.py           # discover_model_paths
│       └── backend.py          # YoloDetector
├── vision/drawing/ ...
├── io/camera/capture.py
└── ui/input/handlers.py
```

Repo root: `main.py`, optional `block_detected.toml`, `models/*.pt`

## Change map

| Goal | Edit here |
|------|-----------|
| Desktop GUI layout / controls | `apps/gui/robo_window.py`, `apps/gui/widgets/`, `apps/gui/theme.py` |
| Frame preprocess (contrast/blur) | `runtime/preprocess.py` |
| Viewport overlays (contours/corners) | `vision/drawing/overlays.py`, `classical.show_*` in config |
| Inference params (iou/imgsz/max_det) | `runtime/config_schema.py`, `detection/yolo/backend.py` |
| Last model persistence | `inference.last_model_name` in TOML; `engine.switch_model()` auto `save_config` |
| Multi detection panel | `apps/gui/widgets/detection_card.py`, `RuntimeStatus.detections` |
| GUI frame worker thread | `apps/gui/worker.py` |
| GUI entry (`block-detected-gui`) | `apps/gui/app.py` |
| Frame read → infer → render pipeline | `runtime/engine.py` |
| Post-inference filters / stability | `runtime/postprocess.py`, `vision/geometry.py` |
| FPS / latency metrics | `runtime/metrics.py` |
| Session state (conf, eval) | `runtime/state.py` |
| Typed config schema + validation | `runtime/config_schema.py` |
| Load/save TOML config | `runtime/config_store.py` |
| Hot-reload vs restart keys | `runtime/config_schema.py` → `RESTART_*_KEYS` |
| Logging + GUI log buffer | `runtime/logging_setup.py` → `get_log_lines()` |
| YOLO result → domain types | `detection/boxes.py` |
| YOLO model load | `detection/yolo/loader.py`, `detection/yolo/backend.py` |
| Domain types | `core/domain.py`, `core/protocols.py` |
| Status bar + FPS line | `vision/drawing/widgets.py` |
| Key bindings | `ui/input/handlers.py` |
| Camera open/switch | `io/camera/capture.py` |
| Filesystem paths | `config/paths.py` |
| Console script / dependencies | `pyproject.toml` → `[project.dependencies]`, `[project.scripts]` |

## Config

- Defaults: `AppConfig.defaults()` in `runtime/config_schema.py`
- Optional file: `block_detected.toml` at repo root (auto-loaded)
- Hot-reload at runtime: confidence, eval mode, `stability.*`
- Requires restart: camera index/resolution, default model file (switch model in-app via `v`)

## GUI

- Primary entry: `python main.py` → `apps/gui/app.py`.
- Default install (`pip install -e .`) includes PySide6 + textual/rich. Pi lite: `requirements-pi.txt` + `pip install -e . --no-deps`.
- Keep PySide6 imports lazy in `apps/gui/app.py` for import-time safety in tests.
- GUI talks to `runtime.WebcamEngine`; do not duplicate YOLO/camera logic in UI code.
- **Log buffer:** GUI reads logs via `get_log_lines()` (thread-safe snapshot). Do **not** read `LogBufferHandler._records` or any `.records` attribute from UI code.
- **Worker shutdown:** Do not set `frame_thread = None` until the `QThread` has finished (`finished` signal or successful `wait()`). If `wait()` times out, keep Start disabled and show stop-pending status. Use run generation guards so stale `frame_ready` / `error` signals do not update the window.
- **OpenCV windows:** GUI worker calls `engine.shutdown(destroy_cv_windows=False)` — never `cv2.destroyAllWindows()` from GUI code.

## Run

```bash
pip install -e .                     # full: GUI + TUI
pip install -e ".[dev]"              # contributor tests
pip install -r requirements-pi.txt && pip install -e . --no-deps   # Pi lite
pip install -e ".[viewer]"           # view_client.py on viewer PC
python main.py              # interactive GUI/TUI picker in terminal
python main.py --gui        # PySide6 desktop
python main.py --tui        # Textual dashboard
block-detected-gui
block-detected-tui
python -m pytest tests/ -q
```

## GSD

- Phase 3: runtime engine + typed config (implemented)
- Phase 4: PySide6 GUI (implemented; default entry)
- Phase 5: GUI/runtime hardening (implemented)
- Phase 6: detection post-processing + temporal stability (in progress)

## Do not edit

- `models/*.pt`
- `.planning/codebase/` (refresh via `/gsd-map-codebase` only)

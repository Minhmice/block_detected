# Agent guide — CV package layout

Read this before editing. The package uses **layered folders** plus a **runtime** layer for engine/config/metrics (GUI-ready).

## Layer diagram

```
apps/          thin orchestration (webcam loop only)
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
├── apps/webcam/app.py          # entry: load config, run engine loop, wire OpenCV window
├── runtime/
│   ├── engine.py               # WebcamEngine — read/infer/render/metrics
│   ├── state.py                # RuntimeState (conf, overlay, eval, history)
│   ├── metrics.py              # FPS + stage latencies
│   ├── config_schema.py        # AppConfig dataclasses + validate + hot/restart keys
│   ├── config_store.py         # load/save TOML (block_detected.toml)
│   ├── detector_loader.py      # load_detector(path) → YoloDetector
│   └── logging_setup.py        # logging + ring buffer for future GUI log panel
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
| Webcam loop / window wiring only | `apps/webcam/app.py` |
| Frame read → infer → render pipeline | `runtime/engine.py` |
| FPS / latency metrics | `runtime/metrics.py` |
| Session state (conf, overlay, eval) | `runtime/state.py` |
| Typed config schema + validation | `runtime/config_schema.py` |
| Load/save TOML config | `runtime/config_store.py` |
| Hot-reload vs restart keys | `runtime/config_schema.py` → `RESTART_*_KEYS` |
| Logging + GUI log buffer | `runtime/logging_setup.py` |
| YOLO result → domain types | `detection/boxes.py` |
| YOLO model load | `detection/yolo/loader.py`, `detection/yolo/backend.py` |
| Domain types | `core/domain.py`, `core/protocols.py` |
| Status bar + FPS line | `vision/drawing/widgets.py` |
| Key bindings | `ui/input/handlers.py` |
| Camera open/switch | `io/camera/capture.py` |
| Filesystem paths | `config/paths.py` |

## Config

- Defaults: `AppConfig.defaults()` in `runtime/config_schema.py`
- Optional file: `block_detected.toml` at repo root (auto-loaded)
- Hot-reload at runtime: confidence, overlay, eval mode (via engine state)
- Requires restart: camera index/resolution, default model file (switch model in-app via `v`)

## Run

```bash
pip install -e ".[dev]"
python main.py
python -m block_detected
python -m pytest tests/ -q
block-detected-webcam
```

## GSD

- Phase 3: runtime engine + typed config (in progress)

## Do not edit

- `models/*.pt`
- `.planning/codebase/` (refresh via `/gsd-map-codebase` only)

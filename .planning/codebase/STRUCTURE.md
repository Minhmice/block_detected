# Codebase Structure

**Analysis Date:** 2026-06-30

## Directory Layout (as implemented)

```
block_detected/                       # Repo root
├── main.py                           # Mode picker + dispatch (view/tui/stream)
├── bootstrap.py                      # Device detect + optional auto-install
├── pyproject.toml                    # Packaging + console scripts + extras
├── README.md                         # Run/install instructions
├── AGENTS.md                         # Dependency rules + change map
├── models/                           # Local YOLO weights (*.pt) discovered at runtime
├── src/
│   ├── block_detected/               # Installable library (runtime + config + core types)
│   │   ├── config/                   # JSON config schema + load/save + validation
│   │   ├── core/                     # Domain types + DetectorBackend protocol
│   │   ├── detection/                # YOLO adapter + parsing
│   │   ├── io/                       # Camera adapters (desktop + Pi)
│   │   ├── runtime/                  # Engine + frame loop + postprocess + render + metrics
│   │   ├── tui/                      # Textual dashboard app (uses runtime)
│   │   └── vision/                   # Geometry + drawing overlays
│   ├── view/                         # OpenCV preview app (uses runtime)
│   ├── stream/                       # Pi JPEG server + LAN viewer (standalone)
│   └── block_detection_v2/           # Legacy/prototype pipeline + dataset (not used by main.py)
├── tests/                            # pytest suite
└── .planning/                        # Project planning + codebase docs
```

## Key Entry Points

- **Launcher**: `main.py`
  - Dispatches to:
    - `src/view/app.py` (`--view`)
    - `src/block_detected/tui/app.py` (`--tui`)
    - `src/stream/__main__.py` (`--stream`)
- **Bootstrap**: `bootstrap.py` (auto-install profile logic)
- **Console scripts**: `pyproject.toml` `[project.scripts]` (e.g. `block-detected-view`, `block-detected-tui`)

## `src/block_detected/` (library + config + TUI)

### Config

- **Schema**: `src/block_detected/config/schema.py` (`AppConfig`, restart key sets)
- **Load/save + migration**: `src/block_detected/config/store.py`
  - Default config location is **inside the package**: `DEFAULT_CONFIG_PATH = PACKAGE_ROOT / "block_detected.json"`
  - Legacy migration from root files: `block_detected.toml`, `block_detected.json`
- **Validation**: `src/block_detected/config/validate.py`
- **Paths/constants**: `src/block_detected/config/paths.py`, `defaults.py`, `camera.py`, `inference.py`, `ui.py`

### Core types & protocols

- `src/block_detected/core/domain.py` (e.g. `RuntimeStatus`, `Detection`)
- `src/block_detected/core/protocols.py` (`DetectorBackend` interface)

### Detection (YOLO)

- `src/block_detected/detection/yolo/backend.py` (Ultralytics inference adapter)
- `src/block_detected/detection/yolo/loader.py` (model discovery / model index resolution)
- `src/block_detected/detection/boxes.py` (YOLO result → `Detection` objects)

### Runtime (shared by View + TUI)

High-level orchestration:

- `src/block_detected/runtime/engine.py` (`WebcamEngine`)

Pipeline stages:

- `src/block_detected/runtime/frame_loop.py` (read → preprocess → infer → postprocess → render → metrics)
- `src/block_detected/runtime/preprocess.py` (contrast/brightness/saturation + blur)
- `src/block_detected/runtime/postprocess.py` (stability + filters)
- `src/block_detected/runtime/render.py` (overlay composition)
- `src/block_detected/runtime/metrics.py` (FPS + stage timing)

Camera session helpers:

- `src/block_detected/runtime/session.py` (open camera; switch camera; Pi source selection)
- `src/block_detected/runtime/platform.py` (Pi detection)

### Vision (geometry + drawing)

- `src/block_detected/vision/geometry.py` (geometry helpers like `box_center`, hit tests)
- `src/block_detected/vision/drawing/widgets.py` (model switch button overlay)
- `src/block_detected/vision/drawing/overlays.py`, `detections.py`, `eval.py`

### TUI app

- `src/block_detected/tui/app.py` (Textual dashboard + runtime controls)

## `src/view/` (OpenCV preview app)

- `src/view/app.py`: owns the OpenCV window loop and delegates detection to `WebcamEngine`
- `src/view/input.py`: keyboard/mouse handling (model switch, confidence changes, reload config)
- `src/view/reload.py`: config reload plumbing (triggered by `r`)

## `src/stream/` (standalone Pi camera stream)

- `src/stream/server.py`: UDP discovery + TCP JPEG streaming
- `src/stream/viewer.py`: Tkinter UI + LAN discovery + OpenCV viewer window
- `src/stream/protocol.py`: wire protocol helpers/constants

## `src/block_detection_v2/` (legacy / experimental)

This appears to be an older or experimental pipeline + dataset and is **not** launched via `main.py`.

Evidence:

- Alternative entrypoint exists: `src/block_detection_v2/main.py`
- Dataset present: `src/block_detection_v2/block_dataset/*.jpg`


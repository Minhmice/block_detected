# Agent guide — CV package layout

Read this before editing. The package uses **layered folders** so new CV features (batch, tracking, ONNX) slot in without flattening everything again.

## Layer diagram

```
apps/          orchestration (webcam loop, future batch/export)
  └── webcam/
config/        constants only — split by domain
core/          shared types — no OpenCV/YOLO imports
detection/     models + inference parsing
  └── yolo/    Ultralytics backend (future: onnx/)
vision/        draw/geometry on frames — no model imports
  └── drawing/
io/            cameras, files, streams
  └── camera/
ui/            keyboard/mouse callbacks
  └── input/
```

**Dependency rule:** `detection` must not import `apps` or `ui`. `vision` must not import `detection`.

## Directory tree

```
src/block_detected/
├── __init__.py
├── __main__.py                 → python -m block_detected
├── apps/
│   ├── webcam/app.py           # main loop ONLY
│   └── batch/__init__.py       # future batch app (stub)
├── config/
│   ├── paths.py                # PROJECT_ROOT, MODELS_DIR, IMAGES_*
│   ├── camera.py               # resolution, camera index
│   ├── inference.py            # conf thresholds, default model name
│   └── ui.py                   # window name, button layout, key codes
├── core/
│   └── types.py                # Box, future Protocol types
├── detection/
│   ├── boxes.py                # result.boxes → list[Box]
│   └── yolo/loader.py          # discover/load .pt
├── vision/
│   ├── geometry.py             # point_in_rect, future transforms
│   └── drawing/
│       ├── overlays.py         # multi-frame trail
│       ├── eval.py             # eval-mode labels
│       └── widgets.py          # status bar, model button
├── io/
│   ├── camera/capture.py       # open_camera, switch_camera
│   └── images/__init__.py      # iter_image_paths (batch input)
└── ui/
    └── input/handlers.py       # handle_key, on_mouse
```

Repo root (outside package): `models/*.pt`, `images/`, `main.py`

## Change map

| Goal | Edit here |
|------|-----------|
| Paths to weights, images, output dirs | `config/paths.py` |
| Camera resolution / default index | `config/camera.py` |
| Confidence limits, default model filename | `config/inference.py` |
| Window title, button size, arrow key codes | `config/ui.py` |
| Re-export config shortcuts | `config/__init__.py` |
| Shared types (Box, future dataclasses) | `core/types.py` |
| Parse YOLO boxes | `detection/boxes.py` |
| Model discovery / load | `detection/yolo/loader.py` |
| New detector backend (ONNX) | `detection/onnx/` (create) |
| Overlay trail colors | `vision/drawing/overlays.py` |
| Eval label style | `vision/drawing/eval.py` |
| Status bar / model button | `vision/drawing/widgets.py` |
| Hit-test geometry | `vision/geometry.py` |
| Webcam open/switch | `io/camera/capture.py` |
| List images in folder (batch input) | `io/images/__init__.py` → `iter_image_paths()` |
| Batch read images / video | `io/video/` (create) |
| Key bindings | `ui/input/handlers.py` |
| Webcam main loop flow | `apps/webcam/app.py` |
| New runnable app (batch) | `apps/batch/app.py` (create) |
| Webcam CLI entry script | `main.py` |
| Batch CLI entry | `pyproject.toml` → `block-detected-batch` |
| Console script name | `pyproject.toml` → `[project.scripts]` |

## Where to add future CV features

| Feature | Location |
|---------|----------|
| Batch folder inference | `apps/batch/app.py` + `io/images/iter_image_paths` |
| RTSP / video file | `io/video/capture.py` |
| Object tracking | `vision/tracking/` |
| Square-box annotator (old batch script) | `vision/drawing/annotators/square.py` |
| Pre/post processing filters | `vision/processing/` |
| Unit tests | `tests/test_*.py` (e.g. `test_geometry.py`, `test_boxes.py`) |

## Conventions

- **Config:** never hardcode paths outside `config/paths.py`
- **Apps:** thin loops — call `detection`, `vision`, `io`, `ui`; no inline `cv2.rectangle`
- **Naming:** avoid package subfolder `models/` (conflicts with repo `models/*.pt`)
- **Logging:** `print("[INFO|WARN|ERROR] ...")` until logging module added
- **Imports:** import submodules directly (`from block_detected.vision.geometry import ...`); keep package `__init__.py` empty of OpenCV/YOLO imports

- **Types:** use `Box` from `core.types` for coordinates

## Run

```bash
pip install -e ".[dev]"
python main.py
python -m pytest tests/ -q
```

## GSD planning

- Phase 2 complete — see `02-VERIFICATION.md`
- Phase 3 planned — batch image inference (`03-*-PLAN.md`)

## Do not edit

- `models/*.pt` — binary weights (gitignored)
- `.planning/codebase/` — refresh with `/gsd-map-codebase` after major structure changes

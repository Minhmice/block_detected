# Codebase Structure

**Analysis Date:** 2026-06-02

## Directory Layout

```
block_detected/
├── main.py                     # CLI entry
├── pyproject.toml
├── requirements.txt
├── block_detected.toml         # optional user config (not committed)
├── AGENTS.md
├── models/                     # *.pt gitignored
├── tests/
└── src/block_detected/
    ├── __main__.py
    ├── apps/webcam/app.py
    ├── runtime/
    │   ├── engine.py
    │   ├── state.py
    │   ├── metrics.py
    │   ├── config_schema.py
    │   ├── config_store.py
    │   ├── detector_loader.py
    │   └── logging_setup.py
    ├── config/
    │   ├── paths.py
    │   ├── camera.py
    │   ├── inference.py
    │   └── ui.py
    ├── core/
    │   ├── types.py
    │   ├── domain.py
    │   └── protocols.py
    ├── detection/
    │   ├── boxes.py
    │   └── yolo/
    │       ├── loader.py
    │       └── backend.py
    ├── vision/
    │   ├── geometry.py
    │   └── drawing/
    ├── io/camera/capture.py
    └── ui/input/handlers.py
```

## Directory Purposes

**`apps/`:** Runnable orchestration only.

**`runtime/`:** Session engine, config, metrics, logging — GUI-ready boundary.

**`config/`:** Path constants and legacy default constants feeding `AppConfig`.

**`detection/yolo/`:** Ultralytics YOLO load + predict.

**`tests/`:** Unit tests without camera or real models.

## Key File Locations

| Concern | Path |
|---------|------|
| Webcam loop wiring | `apps/webcam/app.py` |
| Inference pipeline | `runtime/engine.py` |
| TOML config | `runtime/config_store.py` |
| Model discovery | `detection/yolo/loader.py` |
| YOLO wrapper | `detection/yolo/backend.py` |
| Parse results | `detection/boxes.py` |
| Key bindings | `ui/input/handlers.py` |

## Naming Conventions

- snake_case modules
- `app.py` per application under `apps/<name>/`
- Do not add package subfolder named `models/` (conflicts with repo `models/`)

## Where to Add New Code

| Feature | Location |
|---------|----------|
| GUI panel | New `apps/gui/` or external process reading `AppConfig` + log buffer |
| Video file / RTSP | `io/video/` |
| Tracking | `vision/tracking/` |
| Classical CV stage | Implement `classical` config + `vision/processing/` |
| Tests | `tests/test_<area>.py` |

## Import Convention

Package `__init__.py` in `vision/` and `io/` stay minimal (no OpenCV import at package import time).

---

*Structure analysis: 2026-06-02*

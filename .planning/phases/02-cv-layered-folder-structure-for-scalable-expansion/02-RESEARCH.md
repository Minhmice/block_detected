# Phase 2 Research: CV Layered Folder Structure

**Analysis Date:** 2026-06-02

## RESEARCH COMPLETE

## Standard Stack

- **Python 3.10+** with `src/` layout and `pyproject.toml` (setuptools)
- **Ultralytics YOLO** — detection backend in `detection/yolo/` (future: `detection/onnx/`)
- **OpenCV** — I/O and drawing in `io/` and `vision/`
- **No framework** for apps — thin orchestration in `apps/<name>/app.py`

## Architecture Patterns

**Layered CV package (recommended for this project size → medium scale):**

```
apps/       → runnable pipelines (webcam, export) — orchestration only
config/     → paths, thresholds, UI constants — no business logic
core/       → shared types, protocols, exceptions — no OpenCV/YOLO imports
detection/  → model load, inference, result parsing — depends on ultralytics
vision/     → pure drawing/geometry on numpy frames — no model imports
io/         → camera, video, image read/write — OpenCV capture only
ui/         → keyboard/mouse/window callbacks — depends on vision + config
```

**Dependency rule (enforce for expansion):**
- `apps` → may import all layers
- `detection` → `config`, `core` only (not `apps`, not `ui`)
- `vision` → `core` only (keep drawing testable without YOLO)
- `io` → `config`, `core`
- `ui` → `config`, `vision`, `core`

**Do not** use a top-level folder named `models/` inside the package — conflicts with repo `models/*.pt` weights directory.

## Don't Hand-Roll

- **YOLO inference** — use Ultralytics `YOLO` and `Results`; wrap in `detection/yolo/loader.py`
- **Object detection postprocess** — use `result.boxes` API; parse in `detection/boxes.py`
- **Package discovery** — use setuptools `[tool.setuptools.packages.find] where = ["src"]`
- **Config hierarchy** — split by domain (`paths`, `camera`, `inference`, `ui`), re-export from `config/__init__.py`

## Common Pitfalls

- **Flat `config.py` at package root** — grows unbounded; split early by domain
- **Drawing mixed with inference loop** — hard to add RTSP/video later; keep `apps/webcam/app.py` thin
- **Import cycles** — `ui` importing `detection` for drawing; UI should only call `vision` helpers
- **`PROJECT_ROOT` depth** — when moving files deeper, update `Path(__file__).resolve().parents[N]` in one place (`config/paths.py` only)
- **Console script entry** — update `pyproject.toml` `[project.scripts]` when moving `main()`

## Code Examples

**Single source for project paths:**

```python
# src/block_detected/config/paths.py
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[3]
MODELS_DIR = PROJECT_ROOT / "models"
```

**App entry stays thin:**

```python
# src/block_detected/apps/webcam/app.py
def main() -> int:
    ...
```

## Expansion Roadmap (folders to add later)

| Future feature | Add under |
|----------------|-----------|
| Video file / RTSP | `io/video/` |
| Tracking (ByteTrack, etc.) | `vision/tracking/` |
| ONNX / TensorRT backend | `detection/onnx/` |
| Shared annotators | `vision/drawing/` |
| Unit tests | `tests/` mirroring package tree |

## Confidence

| Claim | Confidence |
|-------|------------|
| Layered layout scales to 10+ CV features | High |
| Ultralytics stays primary detector | High |
| Separate `vision` from `detection` reduces coupling | High |

---

*Research for Phase 2 — CV layered folder structure*

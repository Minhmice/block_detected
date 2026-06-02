# Project State

## Current Position

**Phase:** 4 in progress (desktop GUI)
**Plan:** Phase 4 added — PySide6 GUI on WebcamEngine
**Status:** GUI optional extra + `block-detected-gui`; CLI unchanged

## Accumulated Context

### Roadmap Evolution

- Phase 1: Package foundation (complete)
- Phase 2: CV layered folder structure (complete — 3 plans executed)
- Entry point renamed: `run_yolo_webcam.py` → `main.py`
- Phase 3 added: Runtime engine, typed config, detector abstraction for GUI prep
- Phase 4 added: Desktop GUI for webcam runtime control and config

## Quick Tasks Completed

| Task | Date | Outcome |
|------|------|---------|
| Modular refactor | 2026-06-02 | src/block_detected flat modules |
| Layered CV structure | 2026-06-02 | apps/config/core/detection/vision/io/ui + tests |

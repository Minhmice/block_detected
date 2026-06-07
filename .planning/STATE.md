# Project State

## Current Position

**Phase:** 4 in progress (desktop GUI)
**Plan:** Phase 3 complete (2/2 plans verified); Phase 4 PySide6 GUI on WebcamEngine
**Status:** Runtime engine + typed config verified (31 tests); GUI optional extra + `block-detected-gui`

## Accumulated Context

### Roadmap Evolution

- Phase 1: Package foundation (complete)
- Phase 2: CV layered folder structure (complete — 3 plans executed)
- Entry point renamed: `run_yolo_webcam.py` → `main.py`
- Phase 3: Runtime engine, typed config, detector abstraction (complete — 2 plans, 31 tests)
- Phase 4 added: Desktop GUI for webcam runtime control and config
- Phase 7 added: Web telemetry API and frame streaming for Stitch console (gap analysis 2026-06-07)
- Phase 8 added: YOLO inference params expansion and hot-reload API
- Phase 9 added: Stability and reject rules spec alignment
- Phase 10 added: Camera source types viewport and coordinate mapping
- Phase 11 added: ROI crop stage and preprocessing controls
- Phase 12 added: Classical CV pipeline and overlay layers
- Phase 13 added: Primary target kinematics and tracker state machine
- Phase 14 added: Named config profiles and web config API

## Quick Tasks Completed

| Task | Date | Outcome |
|------|------|---------|
| Modular refactor | 2026-06-02 | src/block_detected flat modules |
| Layered CV structure | 2026-06-02 | apps/config/core/detection/vision/io/ui + tests |

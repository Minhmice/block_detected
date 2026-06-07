# Project State

## Current Position

**Phase:** 8 next (YOLO inference params)
**Plan:** Phase 7 complete (3/3 plans verified); 95 pytest tests passing
**Status:** Web telemetry API + MJPEG streaming for Stitch console complete

## Accumulated Context

### Roadmap Evolution

- Phase 1: Package foundation (complete)
- Phase 2: CV layered folder structure (complete — 3 plans executed)
- Entry point renamed: `run_yolo_webcam.py` → `main.py`
- Phase 3: Runtime engine, typed config, detector abstraction (complete — 2 plans, 31 tests)
- Phase 4: Desktop GUI (complete — 2 plans, GUI offscreen tests)
- Phase 5: GUI/runtime hardening (complete — 2 plans, test_gui_hardening)
- Phase 6: Postprocess + temporal stability (complete — 2 plans, update_config + engine tests)
- Phase 7: Web telemetry API and frame streaming for Stitch console (complete — 3 plans, 9 web API tests)
- Phase 8 added: YOLO inference params expansion and hot-reload API
- Phase 9 added: Stability and reject rules spec alignment
- Phase 10 added: Camera source types viewport and coordinate mapping
- Phase 11 added: ROI crop stage and preprocessing controls
- Phase 12 added: Classical CV pipeline and overlay layers
- Phase 13 added: Primary target kinematics and tracker state machine
- Phase 14 added: Named config profiles and web config API

## Decisions

- Console script remains `block-detected` (no separate `block-detected-gui` alias)
- Manual webcam UAT items documented as optional; autonomous phase closure uses automated pytest only

## Quick Tasks Completed

| Task | Date | Outcome |
|------|------|---------|
| Modular refactor | 2026-06-02 | src/block_detected flat modules |
| Layered CV structure | 2026-06-02 | apps/config/core/detection/vision/io/ui + tests |
| Phases 4–6 retroactive verify | 2026-06-07 | 76 tests; GUI hardening + postprocess coverage |

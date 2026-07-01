# Roadmap: Block Detected

## Overview

**v1.x** — YOLO webcam inference, layered CV package, shared runtime (`WebcamEngine`), View/TUI/Stream apps, postprocess, web telemetry (phases 1–14).

v2.0 classical-CV milestone (phases 15–18, spikes) was removed from planning on 2026-06-30.

## Phases (v1.x)

| # | Phase | Status |
|---|-------|--------|
| 02 | CV layered folder structure | ✓ |
| 03 | Runtime engine + typed config + detector abstraction | ✓ |
| 04 | Desktop GUI for webcam runtime control | ✓ |
| 05 | GUI and runtime hardening for production UAT | ✓ |
| 06 | Detection post-processing + reject rules + temporal stability | ✓ |
| 07 | Web telemetry API + frame streaming | ✓ |
| 08 | YOLO inference params expansion + hot-reload API | deferred |
| 09 | Stability and reject-rules spec alignment | deferred |
| 10 | Camera source types, viewport, coordinate mapping | deferred |
| 11 | ROI crop stage + preprocessing controls | in progress |
| 12 | Classical CV pipeline + overlay layers | deferred |
| 13 | Primary target kinematics + tracker state machine | deferred |
| 14 | Named config profiles + web config API | deferred |
| 15 | Robo-vision desktop GUI (Stitch HTML spec) | deferred |

See `.planning/phases/<nn>-*/` for per-phase CONTEXT, PLAN, and SUMMARY artifacts.

### Phase 2: Dataset Hex Debugger MVP

**Goal:** [To be planned]
**Requirements**: TBD
**Depends on:** Phase 1
**Plans:** 0/1 plans executed

Plans:
- [ ] TBD (run /gsd-plan-phase 2 to break down)

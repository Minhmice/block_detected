# Block Detected

## What This Is

Python computer-vision project for realtime block/object detection. v1 uses YOLO (Ultralytics) with webcam, GUI, and web API. v2 adds a standalone classical-CV hexagon block detector (`block_detection_v2`) using only OpenCV + NumPy.

## Core Value

Reliable realtime block pose from camera: v1 via YOLO; v2 via classical geometry on hexagon contours.

## Requirements

### Validated

- [x] Webcam YOLO inference with model switch, camera switch, eval mode
- [x] Layered CV package, runtime, GUI, postprocess, web telemetry (v1 phases 1–7)

### Active (Milestone v2.0)

- [ ] Standalone `block_detection_v2` module — no v1 imports, no YOLO
- [ ] Hexagon 6-point detection, front/right faces, yaw, EMA tracker, overlay
- [ ] Runnable via `python -m block_detection_v2.main`

### Out of Scope

- Cloud API / auth — local-only inference
- YOLO inside v2 — deferred; TODO for ROI only
- Modifying v1 packages for v2 integration — separate milestone

## Current Milestone: v2.0 Classical CV Block Detection

**Goal:** Greenfield OpenCV-only hexagon block detector as isolated package under `src/block_detection_v2/`.

**Target features:**

- Camera → preprocess → edges → 6-point polygon → geometry (faces, yaw, homography splits)
- EMA temporal stability with jump reject and short hold
- Live overlay + per-frame result dict
- Future YOLO ROI noted as TODO only

## Context

Brownfield v1 at `src/block_detected/`. v2 is intentionally decoupled: classical CV path for block hexagon without neural detector.

## Key Decisions

| Decision | Rationale | Outcome |
|----------|-----------|---------|
| `src/` layout + pyproject.toml | Standard installable package | ✓ Good |
| v2 isolated from v1 | Clean experiment; no YOLO yet | — In progress |
| OpenCV + NumPy only for v2 | Spec requirement | — In progress |

## Evolution

This document evolves at phase transitions and milestone boundaries.

**After each phase transition** (via `/gsd-transition`):
1. Requirements invalidated? → Move to Out of Scope with reason
2. Requirements validated? → Move to Validated with phase reference
3. New requirements emerged? → Add to Active
4. Decisions to log? → Add to Key Decisions
5. "What This Is" still accurate? → Update if drifted

**After each milestone** (via `/gsd-complete-milestone`):
1. Full review of all sections
2. Core Value check — still the right priority?
3. Audit Out of Scope — reasons still valid?
4. Update Context with current state

---
*Last updated: 2026-06-29 — milestone v2.0 started*

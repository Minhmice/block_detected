# Block Detected

## What This Is

Python computer-vision project for realtime block/object detection using YOLO (Ultralytics). Primary app: webcam inference with interactive model switching and overlays.

## Core Value

Reliable realtime detection from webcam with easy model swapping and tunable confidence.

## Requirements

### Validated

- [x] Webcam YOLO inference with model switch, camera switch, eval mode

### Active

- [ ] Scalable CV package layout for future detection, tracking, and training workflows
- [ ] Agent-readable structure docs (AGENTS.md)

### Out of Scope

- Cloud API / auth — local-only inference
- Training pipeline in-repo — use Ultralytics CLI externally for now

## Context

Brownfield: started as single-script YOLO webcam. Refactored to `src/block_detected/` package. Expanding toward full CV monorepo-style layout within one Python package.

## Key Decisions

| Decision | Rationale | Outcome |
|----------|-----------|---------|
| `src/` layout + pyproject.toml | Standard installable package | ✓ Good |
| Layered folders: apps / detection / vision / io / ui | CV expansion without flat module sprawl | — Pending |

---
*Last updated: 2026-06-02 after CV structure phase*

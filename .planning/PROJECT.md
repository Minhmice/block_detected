# Block Detected

## What This Is

Python computer-vision project for realtime block/object detection using YOLO (Ultralytics) with webcam capture, OpenCV View preview, Textual TUI, and optional Pi JPEG stream.

## Core Value

Reliable realtime block detection and pose from camera via a shared `WebcamEngine` runtime.

## Requirements

### Validated

- [x] Webcam YOLO inference with model switch, camera switch, eval mode
- [x] Layered CV package, runtime, GUI, postprocess, web telemetry (v1 phases 1–7)

### Active (Milestone v1.x)

- [ ] Phases 8–14: inference params, stability, camera sources, ROI/preprocess, classical CV overlays, kinematics, config profiles

### Out of Scope

- Cloud API / auth — local-only inference
- Standalone classical-CV v2 milestone (removed from planning)

## Current Milestone: v1.x

**Goal:** Harden and extend the shared `block_detected` runtime and app shells (View, TUI, Stream).

## Context

Brownfield v1 at `src/block_detected/`. Entry via `main.py` → `--view`, `--tui`, or `--stream`.

## Key Decisions

| Decision | Rationale | Outcome |
|----------|-----------|---------|
| `src/` layout + pyproject.toml | Standard installable package | ✓ Good |
| Shared `WebcamEngine` runtime | One pipeline for View + TUI | ✓ Good |
| Stream standalone | Pi JPEG server has no `block_detected` import | ✓ Good |

---
*Last updated: 2026-06-30 — v2 planning removed; codebase map refreshed*

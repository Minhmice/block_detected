---
phase: 02-camera-capture
plan: 03
subsystem: camera
tags: [debug, CAM-03]
requirements-completed: [CAM-03]
completed: 2026-05-31
---

# Phase 02 Plan 03 Summary

**`DebugFrameWriter` saves `{frame_id}_raw.png` with path confinement, retention, and smoke `--save-debug`.**

## Accomplishments

- `debug.py`: `DebugSettings`, `DebugFrameWriter` (sampling, max_files, allowed_root)
- Five green debug tests including traversal rejection
- Smoke script `--save-debug` integration

## Verification

20 tests total (`pytest -q`).

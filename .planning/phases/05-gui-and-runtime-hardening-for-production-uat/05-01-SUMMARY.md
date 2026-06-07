---
phase: 05-gui-and-runtime-hardening-for-production-uat
plan: 01
subsystem: testing
tags: [pyside6, worker-lifecycle, generation-guard]
requires:
  - phase: 04-desktop-gui-for-webcam-runtime-control-and-config
    provides: MainWindow, FrameThread
provides:
  - GUI hardening regression tests for worker shutdown safety
affects: [06-detection-post-processing-reject-rules-and-temporal-stabilit]
tech-stack:
  added: []
  patterns: [run generation guards, stop-pending UX tests]
key-files:
  created: [tests/test_gui_hardening.py]
  modified: []
key-decisions:
  - "Source-level assert for destroy_cv_windows=False instead of running FrameThread"
requirements-completed: [REQ-01, REQ-04]
duration: 12min
completed: 2026-06-07
---

# Phase 5 Plan 01: GUI Hardening Tests Summary

**Run-generation guards, stop-pending UX, and restart hints regression-tested offscreen.**

## Task Commits

1. **Task 1: Run generation guard tests** - `c9466dd`
2. **Task 2: Stop-pending and restart hint tests** - `c9466dd`

## Files Created

- `tests/test_gui_hardening.py` - 7 hardening tests

## Deviations from Plan

None.

## Self-Check: PASSED

- tests/test_gui_hardening.py: FOUND
- Commit c9466dd: FOUND

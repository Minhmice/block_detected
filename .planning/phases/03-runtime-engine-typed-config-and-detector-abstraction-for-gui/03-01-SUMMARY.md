---
phase: 03-runtime-engine-typed-config-and-detector-abstraction-for-gui
plan: 01
subsystem: testing
tags: [pytest, AppConfig, TOML, hot-reload]

requires:
  - phase: 02-cv-layered-folder-structure-for-scalable-expansion
    provides: Layered package layout and pytest foundation
provides:
  - Config schema regression tests for from_dict, validate, restart keys
  - Expanded config_apply and config_store hot-reload coverage
  - REQ-04 requirement registered
affects: [04-desktop-gui, 14-named-config-profiles]

tech-stack:
  added: []
  patterns: [TDD config contract tests without OpenCV/Ultralytics]

key-files:
  created: [tests/test_config_schema.py]
  modified: [tests/test_config_apply.py, tests/test_config_store.py, .planning/REQUIREMENTS.md]

key-decisions:
  - "Stability-only config changes classified as non-restart via needs_runtime_restart tests"

patterns-established:
  - "Config tests use AppConfig.defaults() baseline with field mutation"

requirements-completed: [REQ-02, REQ-04]

duration: 8min
completed: 2026-06-07
---

# Phase 3 Plan 01: Config Test Gaps Summary

**Config schema, store, and apply modules now have explicit regression tests for hot-reload vs restart classification.**

## Performance

- **Duration:** 8 min
- **Tasks:** 3
- **Files modified:** 4

## Accomplishments

- Created `tests/test_config_schema.py` with six behaviors (partial from_dict, unknown keys, validate ordering/IoU, restart classification)
- Expanded `test_config_apply.py` for per-field stability diffs and hot stability apply
- Expanded `test_config_store.py` for extra TOML section tolerance
- Registered REQ-04 in REQUIREMENTS.md

## Task Commits

1. **Task 1–3: Config tests + REQ-04** - `061957e` (test)

## Files Created/Modified

- `tests/test_config_schema.py` - Dedicated AppConfig unit tests
- `tests/test_config_apply.py` - Stability hot-reload classification tests
- `tests/test_config_store.py` - Extra TOML section tolerance test
- `.planning/REQUIREMENTS.md` - REQ-04 runtime requirement

## Deviations from Plan

None - plan executed exactly as written.

## Self-Check: PASSED

- FOUND: tests/test_config_schema.py
- FOUND: commit 061957e

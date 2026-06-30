---
phase: 01-core-cv-pipeline
plan: 02
type: execute
tags: [temporal, hold, debug, rendering, score-breakdown]
requires: ["01-01"]
provides: ["guarded-hold", "debug-modes", "score-breakdown"]
tech-stack:
  added: []
  patterns:
    - "Single-advance hold_age via try_hold() with rollback on guard failure"
    - "Basic/verbose debug payload via _build_debug_payload() respecting HexDetectorConfig.debug_mode"
    - "Renderer draws winning_lines always, grouped lines only in verbose"
key-files:
  created:
    - src/hex_detector/tracker.py
    - src/hex_detector/renderer.py
    - tests/test_hex_detector_temporal_debug.py
  modified:
    - src/hex_detector/config.py
    - src/hex_detector/detector.py
decisions:
  - "hold_iou_threshold=0.5, hold_score_decay=0.8, max_hold_frames=3"
  - "hold_bbox_center_jump_ratio=0.3, hold_bbox_size_change_ratio=0.5"
  - "hold_point_conflict_threshold=0.3, debug_top_candidates=5"
  - "debug_mode defaults to basic for Pi 5 performance"
  - "hold_age rolls back on guard failure to prevent phantom aging"
  - "prune_missing only prunes stale state, never increments hold_age"
metrics:
  tasks: 3
  commits: 3
  test_count: 31 (8 front_modes + 23 temporal_debug)
  files_changed: 5 (+952, -14)
  duration: ""
---

# Phase 1 Plan 2: Temporal hold, score diagnostics, and Pi-friendly rendering

**One-liner:** Guarded one-tick-per-frame hold-last-good with multiplicative score decay, typed ScoreBreakdown on every result, and basic/verbose debug rendering that defaults to winner-only geometry.

## What was built

1. **Guarded hold-last-good state machine** (`tracker.py`): Single `try_hold()` operation that increments `hold_age` exactly once per frame, validates IoU >= 0.5, bbox center/size jump limits, and prunes after 3 frames. Present-track CV failures and missing YOLO tracks both flow through the same guarded operation. Score decays via `last_good_score * 0.8^age`.

2. **Configurable hold parameters** (`config.py`): `hold_iou_threshold=0.5`, `hold_score_decay=0.8`, `max_hold_frames=3`, plus bbox center jump (0.3×diagonal) and size change (50%) limits. `debug_mode` with values `basic|verbose` and `debug_top_candidates=5`.

3. **Typed debug payloads** (`detector.py`): `_build_debug_payload()` builds per-result debug dicts. Basic mode includes `winning_lines` and `roi_size` only. Verbose mode adds `groups` (all merged line groups). Every result carries a `ScoreBreakdown` with 6 named fields; rejected results get zeroed breakdowns.

4. **Pi-friendly default renderer** (`renderer.py`): Always draws bbox, winning geometry edges, A-F points, status/score label, and rejection code. Grouped-line drawing triggers only when `groups` key is present in debug (verbose mode). Held status highlighted in yellow.

## Tasks completed

| # | Name | Commit | Key files |
|---|------|--------|-----------|
| 1 | Temporal/debug/renderer contract tests | `c12e07f` | `tests/test_hex_detector_temporal_debug.py` |
| 2 | Guarded hold-last-good state machine | `a209bb0` | `config.py`, `tracker.py`, `detector.py` |
| 3 | Typed debug payloads + basic/verbose rendering | `af742df` | `detector.py`, `renderer.py` |

## Verification

```
python -m pytest tests/test_hex_detector_front_modes.py tests/test_hex_detector_temporal_debug.py -q
31 passed
```

All must-have truths (D-04 through D-14) verified:
- D-04: Hold from present-track CV failure and YOLO miss ✓
- D-05: Hold requires same track ID, IoU >= 0.5, age <= 3, no bbox jump ✓
- D-06: Held status + score = last_good * 0.8^age ✓
- D-07: New tracks, low IoU, large jumps reject hold ✓
- D-12: Basic debug includes only winning geometry; verbose adds grouped lines ✓
- D-13: Every result exposes edge_support, parallelism, topology, area_position, temporal, total ✓
- D-14: Default rendering draws winning geometry only, not all grouped lines ✓

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 2 - Missing Critical Behavior] Zeroed ScoreBreakdown on rejected results**
- **Found during:** Task 2
- **Issue:** `_make_base()` returned `DetectionResult` with `score_breakdown=None`, but plan mandates every result carries a `ScoreBreakdown`.
- **Fix:** Added zeroed `ScoreBreakdown(edge_support=0, parallelism=0, topology=0, area_position=0, temporal=0, total=0)` to all rejected result paths.
- **Files modified:** `src/hex_detector/detector.py`
- **Commit:** `a209bb0`

**2. [Rule 2 - Missing Critical Behavior] hold_age rollback on guard failure**
- **Found during:** Task 2
- **Issue:** Without rollback, a guard-failing frame would permanently advance `hold_age`, causing premature hold expiration and skewing score decay.
- **Fix:** `try_hold()` rolls back `hold_age -= 1` when IoU, bbox jump, or other guards reject the hold. Only successful holds advance the counter.
- **Files modified:** `src/hex_detector/tracker.py`
- **Commit:** `a209bb0`

## Known Stubs

None — all data flows are wired end-to-end. The `debug_top_candidates` config field exists but per-plan intent candidate collection is bounded to the winner in basic mode and the `groups` struct in verbose mode suffices for Pi 5 debugging.

## Threat Flags

None — all threats in the plan's `<threat_model>` are mitigated as designed:
- HIGH stale geometry: IoU >= 0.5 gate + bbox jump check ✓
- HIGH stale persistence: 3-frame cap with score decay ✓
- MEDIUM confidence laundering: `status=held` explicitly marked, rejection reason preserved in debug ✓
- MEDIUM debug CPU: basic is default, verbose only stores groups (no unbounded collections) ✓

## Self-Check: PASSED

- [x] `tests/test_hex_detector_temporal_debug.py` exists
- [x] `src/hex_detector/tracker.py` committed
- [x] `src/hex_detector/renderer.py` committed
- [x] All 3 commits verified: `c12e07f`, `a209bb0`, `af742df`
- [x] 31 tests pass across both test files

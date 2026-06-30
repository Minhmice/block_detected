---
phase: 01-core-cv-pipeline
verified: 2026-06-30T12:14:00Z
status: human_needed
score: 14/14 must-haves verified
overrides_applied: 0
human_verification:
  - test: "Render debug overlay on a real camera frame with and without verbose mode"
    expected: "Basic mode draws bbox, winning geometry edges, A-F points, status label, score, and rejection reason. Verbose mode additionally draws all grouped lines. Held status rendered in yellow. Coordinates converted to integer only at the OpenCV call boundary."
    why_human: "Rendering output requires visual inspection — OpenCV pixel drawing correctness cannot be confirmed via grep."
  - test: "Run detect_frame on real camera frames with actual YOLO detections"
    expected: "Rectangle mode returns when front face is visible but right face is obscured. Hex mode returns when both front and right faces are clear. Rejection codes match the observed failure mode (e.g. NO_FRONT_FACE for heavily occluded blocks)."
    why_human: "Deterministic tests use mock line fixtures; real-frame behavior with varying lighting, angles, and occlusions needs visual confirmation."
  - test: "Run pipeline on Raspberry Pi 5 and verify CPU/memory budget"
    expected: "Basic debug mode stays within Pi 5 CPU bounds. Hold state machine does not leak memory for stale tracks."
    why_human: "Pi 5 performance profiling requires the target hardware — cannot verify via grep or CI tests."
---

# Phase 01: Core CV Pipeline — Verification Report

**Phase Goal:** Module `hex_detector` detect hex/rectangle từ single frame + YOLO bbox
**Verified:** 2026-06-30T12:14:00Z
**Status:** human_needed
**Re-verification:** No — initial verification

## Goal Achievement

### Observable Truths

| #    | Truth | Status     | Evidence |
| ---- | ----- | ---------- | -------- |
| D-01 | A valid A-B-E-F front quadrilateral can produce rectangle mode without C or D lines | ✓ VERIFIED | `detect_roi()` lines 262-297: returns rectangle when best hex is absent/below rectangle score. `pick_front_line_combinations()` requires only 2 vertical + 2 front-horizontal. Test `test_rectangle_from_front_only_lines` passes. |
| D-02 | A valid front face upgrades to hex only when right face has valid support; invalid front returns not_detected | ✓ VERIFIED | `detect_roi()` lines 190-214: hex upgrade loop requires vaild C, D from right combos. Lines 138-141: no front → NO_FRONT_FACE → not_detected. Lines 217-218: INVALID_TOPOLOGY → not_detected. |
| D-03 | Rectangle results contain C=None and D=None and never synthesize those points | ✓ VERIFIED | `points_from_front_lines()` lines 101-104: C=None, D=None hardcoded. Detector lines 268-269, 278-279: explicit C=None, D=None in rectangle path. Test asserts `C is None` and `D is None`. |
| D-04 | Last-good geometry can be held when the same track remains but CV rejects, and when YOLO temporarily omits the track | ✓ VERIFIED | Detector lines 72-77: CV failure → `tracker.try_hold()`. Lines 79-83: missing track → `tracker.try_hold(tid)`. `try_hold()` lines 119-176 handles both paths. Tests `test_cv_failure_returns_held` and `test_missing_track_returns_held` pass. |
| D-05 | Hold requires same track identity, last-good/current bbox IoU >= 0.5, age <= 3 frames, and no configured bbox jump | ✓ VERIFIED | Tracker lines 137-143: must have track state + last_good. Lines 146-148: age gate (`hold_age > max_hold_frames`). Lines 153-154: IoU gate. Lines 157-159: bbox jump gate. All guard failures roll back `hold_age`. Tests `test_no_hold_low_iou`, `test_no_hold_new_track_id` pass. |
| D-06 | Held results use status=held and score = last_good_score * (0.8 ** hold_age) | ✓ VERIFIED | Tracker line 161: `decayed = last_good_result.score * (0.8 ** hold_age)`. Lines 162-176: `status="held"`, `score=decayed`. Test `test_decay_ages_1_2_3_then_prunes` verifies exact 0.8, 0.64, 0.512 sequence. |
| D-07 | New tracks, low-IoU boxes, large jumps, and strongly conflicting new geometry are never replaced by stale held geometry | ✓ VERIFIED | Tracker lines 137-139: no state → None (new track). Lines 153-156: low IoU → None + rollback. Lines 157-159: jump → None + rollback. `store_result()` resets `hold_age=0` on fresh detection. Tests ensure clean rejection. |
| D-08 | HexDetector.detect_frame accepts a Sequence[YoloDetection] and returns typed HexResult values | ✓ VERIFIED | `detect_frame()` signature line 52-56: `Sequence[YoloDetection] -> list[DetectionResult]`. `HexResult = DetectionResult` alias in models.py line 168. Test `test_detect_frame_accepts_sequence` passes. |
| D-09 | detect_frame delegates per-ROI work to an internal detect_roi method | ✓ VERIFIED | Detector line 67: `result = self.detect_roi(frame, det.track_id, smoothed, w, h)`. `detect_roi()` defined at lines 88-95. Test `test_detect_roi_exists` passes. |
| D-10 | Geometry remains float-valued throughout detection and is converted to int only by rendering | ✓ VERIFIED | All models use `float` (BBox, LineSegment, HexPoints). `renderer.py` line 34: `_draw_line` converts via `int(ln.x1)`. Line 81: `int(pt[0]), int(pt[1])` — int conversion only at OpenCV boundary. |
| D-11 | Rejections use stable machine-readable codes including NO_LINES, NO_FRONT_FACE, INVALID_TOPOLOGY, LOW_EDGE_SUPPORT, LOW_SCORE, and ROI_EMPTY | ✓ VERIFIED | `RejectReason` literal in models.py lines 14-21: all six codes. Detector maps: `ROI_EMPTY` (126), `NO_LINES`/`NO_FRONT_FACE` (140), `INVALID_TOPOLOGY` (218), `LOW_EDGE_SUPPORT` (225), `LOW_SCORE` (260). |
| D-12 | Basic debug includes only winning geometry while verbose debug adds grouped lines and bounded top candidates | ✓ VERIFIED | `_build_debug_payload()` lines 299-313: `winning_lines` always; `groups` only when `debug_mode == "verbose"`. Tests `test_basic_debug_has_winner_but_no_top_candidates` and `test_verbose_debug_has_grouped_lines_and_bounded_candidates` pass. |
| D-13 | Every result exposes edge_support, parallelism, topology, area_position, temporal, and total scores | ✓ VERIFIED | `ScoreBreakdown` dataclass lines 25-42 has all 6 fields. `_make_base()` (lines 112-121) returns zeroed breakdown for rejected. Hex path (249) and rectangle path (290) attach breakdown. Tests verify all 6 fields present and total equals weighted sum. |
| D-14 | Default rendering does not draw every grouped line | ✓ VERIFIED | Renderer lines 65-68: always draws `winning_lines`. Lines 71-75: `groups` drawn only when `"groups" in dbg` (verbose mode). Test `test_basic_rendering_draws_less_than_all_grouped_lines` passes. |

**Score:** 14/14 truths verified

### Required Artifacts

| Artifact | Expected | Status | Details |
| -------- | -------- | ------ | ------- |
| `src/hex_detector/models.py` | `ScoreBreakdown`, `DetectionStatus`, `RejectReason`, `HexResult` | ✓ VERIFIED | All present. `ScoreBreakdown` at line 25-42 with 6 fields. `RejectReason` literal at line 14-21 with all 6 codes. `HexResult = DetectionResult` alias at line 168. Exists, substantive, wired into detector/tracker/renderer. |
| `src/hex_detector/config.py` | `max_front_candidates`, `max_right_candidates`, `min_edge_support_score`, `hold_iou_threshold`, `hold_score_decay`, `max_hold_frames`, `debug_mode`, `debug_top_candidates` | ✓ VERIFIED | All config fields present with documented defaults. `validate()` at lines 89-132 enforces all constraints. Wired into detector, tracker, and renderer. |
| `src/hex_detector/lines.py` | `pick_front_line_combinations` | ✓ VERIFIED | Lines 159-195: requires 2+ vertical + 2 front-horizontal. Bounded by `max_front_candidates`. Rightmost vertical reserved when 3+. Imported and called in `detect_roi()`. |
| `src/hex_detector/geometry.py` | `validate_front_points`, `score_front_candidate`, `score_hex_candidate` | ✓ VERIFIED | `validate_front_points` at lines 108-164 with convex/parallel/area checks. `score_front_candidate` at lines 450-493 returns full `ScoreBreakdown`. `score_hex_candidate` at lines 496-526. All imported and used in `detect_roi()`. |
| `src/hex_detector/detector.py` | `HexDetector`, `detect_frame`, `detect_roi` | ✓ VERIFIED | `HexDetector` class line 46. `detect_frame` line 52 accepts `Sequence[YoloDetection]`. `detect_roi` line 88 is the internal per-ROI method. All PIPE-01..10 stages connected in `detect_roi()`. |
| `src/hex_detector/tracker.py` | `hold_age`, `try_hold`, guarded hold state machine | ✓ VERIFIED | `_TrackState.hold_age` line 78. `try_hold()` lines 119-176 with single-advance + rollback. `prune_missing` lines 178-184 only prunes stale state, does not increment age. |
| `src/hex_detector/renderer.py` | `render_debug` with basic/verbose modes | ✓ VERIFIED | `render_debug()` lines 49-109. Always draws bbox, winning edges, A-F points, status/score label, rejection code. Grouped lines only in verbose mode. Held status highlighted yellow. |
| `tests/test_hex_detector_front_modes.py` | Rectangle, hex, rejected, empty-ROI, candidate-cap, API tests | ✓ VERIFIED | 8 tests across 5 classes. Covers rectangle, hex, no-front, no-lines, empty-ROI, candidate caps, and API contract. All pass. |
| `tests/test_hex_detector_temporal_debug.py` | Hold, decay sequence, guards, score breakdown, debug modes, renderer, config validation | ✓ VERIFIED | 23 tests across 8 classes. Covers CV-failure hold, YOLO-miss hold, decay sequence, single-advance, IoU/jump/ID rejection, score fields, basic/verbose debug, renderer defaults, config defaults. All pass. |

### Key Link Verification

| From | To | Via | Status | Details |
| ---- | -- | --- | ------ | ------- |
| `detector.py` | `lines.py` | `pick_front_line_combinations` | ✓ WIRED | Import line 25, call line 137 |
| `detector.py` | `geometry.py` | `validate_front_points` / `score_candidate` | ✓ WIRED | Imports lines 11-18, `validate_front_points` called line 162, `score_front_candidate` line 173, `score_hex_candidate` line 201 |
| `detector.py` | `models.py` | `HexResult` | ✓ WIRED | `DetectionResult` used throughout `detect_roi()`. `HexResult = DetectionResult` alias in models.py line 168 |
| `detector.py` | `tracker.py` | `hold` | ✓ WIRED | `HexTracker` import line 39. `try_hold()` called lines 73, 81 |
| `renderer.py` | `models.py` | `ScoreBreakdown` / `debug` | ✓ WIRED | `DetectionResult` imported line 10. Consumes `res.debug` dict lines 62-75, `res.score` line 90, `res.score_breakdown` attached |
| `config.py` | `tracker.py` | `hold_iou_threshold` / `hold_score_decay` | ✓ WIRED | Tracker accesses `self.cfg.hold_iou_threshold` (154), `self.cfg.hold_score_decay` (161), `self.cfg.max_hold_frames` (147) |

### Data-Flow Trace (Level 4)

| Artifact | Data Variable | Source | Produces Real Data | Status |
| -------- | ------------- | ------ | ------------------ | ------ |
| `detect_roi()` | `front_combos` | `pick_front_line_combinations(groups, cfg)` | Yes (real combinatorics from line groups) | ✓ FLOWING |
| `detect_roi()` | `results` (DetectionResult) | `ScoreBreakdown` from `score_front_candidate`/`score_hex_candidate` | Yes (weighted sum of 5 component scores) | ✓ FLOWING |
| `render_debug()` | `winning_lines` | `debug["winning_lines"]` from `_build_debug_payload()` | Yes (actual line segments from best candidate) | ✓ FLOWING |
| `try_hold()` | `held` (DetectionResult) | `last_good_result` decayed by `0.8^age` | Yes (real score from real prior detection) | ✓ FLOWING |

### Behavioral Spot-Checks

| Behavior | Command | Result | Status |
| -------- | ------- | ------ | ------ |
| All focused tests pass | `python -m pytest tests/test_hex_detector_front_modes.py tests/test_hex_detector_temporal_debug.py -q` | `31 passed in 0.20s` | ✓ PASS |
| Rectangle from front-only lines | Mock test `test_rectangle_from_front_only_lines` | mode=rectangle, C=None, D=None | ✓ PASS |
| Hex from front + right lines | Mock test `test_hex_from_front_and_right_lines` | mode=hex, all A-F finite | ✓ PASS |
| Hold score decay sequence | Mock test `test_decay_ages_1_2_3_then_prunes` | Exact 0.8, 0.64, 0.512 | ✓ PASS |

### Probe Execution

| Probe | Command | Result | Status |
| ----- | ------- | ------ | ------ |
| (none declared) | N/A | N/A | ? SKIP — no probes declared in PLAN or SUMMARY files |

### Requirements Coverage

| Requirement | Source Plan | Description | Status | Evidence |
| ----------- | ---------- | ----------- | ------ | -------- |
| PIPE-01..10 | 01-01-PLAN.md | Pipeline stages in `detect_roi()` | ⚠️ DECLARED ONLY | All 10 stages present in `detect_roi()` (ROI crop → edge prep → raw lines → filter → group → merge → front combos → front validation → right upgrade → scoring). But IDs not defined in `.planning/REQUIREMENTS.md`. |
| MODE-01..03 | 01-01, 01-02 PLAN | Detection modes: rectangle, hex, not_detected | ⚠️ DECLARED ONLY | All 3 modes implemented and tested. `DetectionMode = Literal["hex", "rectangle", "not_detected"]` in models.py. But IDs not defined in REQUIREMENTS.md. |
| OUT-01 | 01-01, 01-02 PLAN | Output contract: `HexResult` with typed fields | ⚠️ DECLARED ONLY | `DetectionResult`/`HexResult` with status, mode, score, score_breakdown, reject_reason, debug. `to_dict()` serializes all. But ID not defined in REQUIREMENTS.md. |
| DBG-01 | 01-02-PLAN.md | Debug modes: basic/verbose | ⚠️ DECLARED ONLY | `debug_mode` with `basic|verbose` values. `_build_debug_payload()` respects mode. But ID not defined in REQUIREMENTS.md. |
| CFG-01 | 01-01, 01-02 PLAN | Central config: all tunables in `HexDetectorConfig` | ⚠️ DECLARED ONLY | `HexDetectorConfig` contains all parameters. `validate()` enforces constraints. No magic numbers in detector paths. But ID not defined in REQUIREMENTS.md. |

**Note:** All 15 requirement IDs (PIPE-01..10, MODE-01..03, OUT-01, DBG-01, CFG-01) are declared in PLAN frontmatter and referenced in CONTEXT.md as belonging to `.planning/REQUIREMENTS.md`, but the actual REQUIREMENTS.md file contains only high-level milestone themes and does not define any of these IDs. This is a documentation gap — the implementation fulfills all declared behaviors, but the requirement traceability chain is incomplete. This does not block goal achievement but should be corrected in REQUIREMENTS.md for auditability.

### Anti-Patterns Found

| File | Line | Pattern | Severity | Impact |
| ---- | ---- | ------- | -------- | ------ |
| (none) | - | - | - | No anti-patterns detected. No TODO/FIXME/XXX/TBD markers. No placeholder implementations. No stub code. |

### Human Verification Required

#### 1. Render Debug Overlay Visual Inspection

**Test:** Render `render_debug(frame, results)` output on a real camera frame. Check basic mode (default) and verbose mode.
**Expected:**
- Basic: Bbox rectangle, winning geometry edges (4-7 lines in distinct group colors), A-F points labeled, status+score text label, rejection reason text when applicable
- Verbose: All grouped lines drawn (vertical=cyan, front-horizontal=orange, right-diagonal=magenta) in addition to winning edges
- Held status: Label displayed in yellow
- All coordinates rendered correctly in frame pixel space
**Why human:** OpenCV pixel drawing cannot be verified via grep. Requires visual confirmation of line placement, color correctness, and label positioning.

#### 2. Real-Frame Detection Quality

**Test:** Run `HexDetector.detect_frame()` on real camera frames with actual YOLO detections. Test with blocks at varying angles, occlusions, and lighting.
**Expected:**
- Rectangle mode fires when front face (A-B-E-F) is visible but right face (B-C-D-E) is obscured or angled away
- Hex mode fires when both front and right faces are clearly visible with distinctive line edges
- `not_detected` + `RejectReason` matches the observed failure (e.g., `NO_FRONT_FACE` for heavily occluded blocks, `LOW_EDGE_SUPPORT` for blurry/faint edges)
- No false C/D synthesis when right face is absent
**Why human:** Deterministic test suite uses mock line fixtures with perfect geometry. Real frames introduce noise, variable lighting, partial occlusions, and varying line density that mock data cannot cover.

#### 3. Raspberry Pi 5 Performance Budget

**Test:** Run full pipeline (`detect_frame` + `render_debug`) on Raspberry Pi 5 with basic debug mode. Monitor CPU usage and memory over a sustained session (5+ minutes).
**Expected:**
- Basic debug mode stays within Pi 5 CPU budget for real-time processing
- Hold state machine does not leak `_TrackState` objects — `prune_missing` removes stale tracks after `max_hold_frames` expiry
- `_build_debug_payload` does not accumulate memory in verbose mode beyond `debug_top_candidates` entries
**Why human:** Pi 5 performance profiling requires the target hardware. Memory leak detection requires sustained runtime observation, not static analysis.

### Gaps Summary

No implementation gaps found. All 14 must-have truths verified through codebase evidence, all 9 required artifacts exist and are fully wired, all 6 key links confirmed connected, and all 31 focused tests pass (0.20s).

**One documentation gap:** Requirement IDs (PIPE-01..10, MODE-01..03, OUT-01, DBG-01, CFG-01) are declared in PLAN frontmatter but not defined in `.planning/REQUIREMENTS.md`. The implementation fulfills all behaviors these IDs represent, but the formal requirement traceability is incomplete. Recommend adding these IDs to REQUIREMENTS.md with descriptions reflecting the implemented pipeline contract.

**Three human verification items** remain for visual output validation, real-frame detection quality, and Pi 5 performance profiling — none are automatable via static analysis or mock tests.

---

_Verified: 2026-06-30T12:14:00Z_
_Verifier: Claude (gsd-verifier)_

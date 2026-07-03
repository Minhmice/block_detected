---
phase: 01-core-cv-pipeline
fixed_at: 2026-07-01
scope: src/hex_detector P1 fixes from VERIFY_REPORT
tests: 50 passed
---

# FIX_REPORT — hex_detector P1 Remediation

## Summary

Implemented all P1 items from `VERIFY_REPORT.md` without changing the public API contract (`HexDetector.detect_frame`, `YoloDetection`, `DetectionResult` / `HexResult`).

---

## Changes by Area

### 1. Hex acceptance gates

**Files:** `detector.py`

**Before:** Hex could win over rectangle with only `best_hex_score >= best_rect_score`; no `min_edge_support_score` or `accept_score_threshold` on hex path.

**After:** Hex accepted only when:
- `best_hex_score >= best_rect_score`
- `hex_breakdown.edge_support >= min_edge_support_score`
- `best_hex_score >= accept_score_threshold`

Otherwise falls back to rectangle (if front valid) or `not_detected`.

**Tests:** `TestHexAcceptanceGates` in `tests/test_hex_detector_p1_fixes.py`

---

### 2. Line grouping (single group, min angular error)

**Files:** `lines.py`

**Before:** `classify_line_group` returned first matching tolerance bucket → overlap could assign duplicate semantics.

**After:** Each line assigned to **one** group — smallest angular error among groups within tolerance. Returns `(group, error)`; `group_lines` logs classifications and optional `logging.DEBUG` when `line_group_log_enabled=True`.

**Tests:** `TestLineGrouping`

---

### 3. Front candidates (no rightmost reserve)

**Files:** `lines.py`

**Before:** With ≥3 verticals, rightmost vertical skipped as BE (reserved for CD).

**After:** All pairs `(AF, BE)` with `AF` left of `BE` (`_vertical_sort_key(AF) < _vertical_sort_key(BE)`), capped by `max_front_candidates`. Score decides winner.

**Tests:** `TestFrontCandidates`

---

### 4. Multi-ratio bottom crop

**Files:** `config.py`, `preprocessing.py`, `detector.py`

**Before:** Single `block_crop_bottom_ratio=0.22`.

**After:**
- `block_crop_bottom_ratios: tuple = (0.0, 0.1, 0.18, 0.22)`
- `max_crop_ratio_attempts: int = 4`
- `detect_roi` tries each ratio, picks best attempt by mode/score
- Debug: `winning_crop_ratio`, `crop_ratio_scores` (verbose)

**Tests:** `TestCropRatios`

---

### 5. Temporal hold — point conflict

**Files:** `tracker.py`, `geometry.py`, `detector.py`

**Before:** `hold_point_conflict_threshold` unused.

**After:** `try_hold(..., candidate_frame_points=..., frame_w=..., frame_h=...)` rejects hold when `frame_points_conflict()` exceeds threshold. Rejected results with valid front attach `candidate_frame_points` in debug for hold evaluation.

**Tests:** `TestHoldConflict`

---

### 6. Verbose debug payload

**Files:** `debug_serialize.py` (new), `detector.py`, `renderer.py`

**Verbose mode exposes (JSON-safe, no ndarray):**
- `raw_lines`, `filtered_lines`, `grouped_lines`, `merged_lines`
- `winning_lines`, `top_candidates`, `validation_results`
- `crop_ratio`, `stage_timings_ms`, `edge_map` (metadata only)
- `line_classifications`, `crop_ratio_scores`

Edge map: `{width, height, edge_pixel_ratio}` only.

**Tests:** `TestVerboseDebug`

---

### 7. Cleanup

| Item | Action |
|------|--------|
| `HexDetector.stale_track_ids()` | Added public API |
| `tracker._tracks` in detector | Replaced with `stale_track_ids()` |
| `should_use_rectangle_mode` | Wired in hex upgrade loop |
| `pick_line_combinations` | Removed from `lines.py` |
| `score_candidate` | Removed from `geometry.py` |
| `clamp_bbox_to_frame` | Removed from `preprocessing.py` |
| `frame_to_roi_point` | Removed from `geometry.py` |
| `max_candidates` config | Removed |
| `batch_hex_son_down.py` | Persistent `HexDetector`, `model.track(persist=True)`, ByteTrack IDs |

---

## New / Changed Config

| Key | Default | Description |
|-----|---------|-------------|
| `block_crop_bottom_ratios` | `(0.0, 0.1, 0.18, 0.22)` | Crop ratios to try |
| `max_crop_ratio_attempts` | `4` | Max ratios per ROI |
| `line_group_log_enabled` | `False` | DEBUG log for line classification |

**Removed:** `block_crop_bottom_ratio`, `max_candidates`

---

## Behavior Before / After

| Scenario | Before | After |
|----------|--------|-------|
| Hex low edge support, good rect | Hex could win | Rectangle |
| Hex score below accept threshold | Hex could win | `not_detected` or rectangle |
| 3 vertical lines | Rightmost never BE | All left-right pairs scored |
| Pallet crop | Fixed 22% | Best of configured ratios |
| CV fail + conflicting geometry | Hold anyway | Hold blocked |
| Multi-crop attempts | N/A | Smoothing applied once on winning crop only |
| Batch script | New detector per image, index IDs | Persistent detector + ByteTrack |

---

## Test Results

```bash
python -m pytest tests/test_hex_geometry.py \
  tests/test_hex_detector_front_modes.py \
  tests/test_hex_detector_temporal_debug.py \
  tests/test_hex_detector_p1_fixes.py -q
# 50 passed
```

---

## Files Touched

- `src/hex_detector/config.py`
- `src/hex_detector/preprocessing.py`
- `src/hex_detector/lines.py`
- `src/hex_detector/geometry.py`
- `src/hex_detector/detector.py`
- `src/hex_detector/tracker.py`
- `src/hex_detector/debug_serialize.py` (new)
- `src/hex_detector/renderer.py`
- `scripts/batch_hex_son_down.py`
- `tests/test_hex_detector_p1_fixes.py` (new)
- `tests/test_hex_detector_front_modes.py`
- `tests/test_hex_detector_temporal_debug.py`

---

_Fixed: 2026-07-01_

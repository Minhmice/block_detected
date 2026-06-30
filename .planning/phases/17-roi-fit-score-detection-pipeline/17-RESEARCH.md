# Phase 17 Research: ROI-fit-score detection pipeline

**Researched:** 2026-06-29
**Source:** Spike experiments 001–004 (pre-validated; no additional web research required)

## RESEARCH COMPLETE

## Summary

Spikes proved contour-only detection is infeasible for this dataset. The build path is ROI-seed + dominant-angle line refinement + composite scoring, ported from `.planning/spikes/shared/block_spike_lib.py`.

## Key Findings

| Area | Verdict | Evidence |
|------|---------|----------|
| ROI silhouette | VALIDATED | 108/108 ROI found; morph 9×9 + pallet mask 78% |
| Line fit | PARTIAL | 108/108 fitted via ROI-seed; pure fixed-angle Hough 0/108 |
| Scoring | VALIDATED | 91/108 accept; blocks 21 legacy label FPs |
| Benchmark | VALIDATED | Harness + overlays; 84% vs 25% baseline |

## Implementation Approach

### New modules (recommended split)
1. `roi.py` — `extract_cluster_roi()`, `ROIBox` dataclass
2. `fit.py` — `fit_hexagon_from_lines()`, `_hex_from_roi()`, `_refine_with_lines()`
3. `score.py` — `score_candidate()`, `edge_support()`, `validate_topology(strict=)`
4. `benchmark.py` or `scripts/bench_v2.py` — port spike 004

### main.py changes
```python
edges, lines = detect_edges(gray)
roi = extract_cluster_roi(edges, color.shape[:2], block_mode=3)
masked = cv2.bitwise_and(edges, roi.mask) if roi else edges
points = fit_hexagon_from_lines(roi_lines, roi, shape, edges=masked) if roi else None
score = score_candidate(points, masked, roi) if points else 0.0
```

### Config additions
- `BLOCK_MODE = 3`
- `ROI_PALLET_FRAC = 0.78`
- `ROI_RIGHT_TRIM_FRAC = 0.22`
- `SCORE_AREA_RATIO_MIN = 0.12`
- `SCORE_HEX_AREA_MIN = 3500`
- `DETECTION_SCORE_MIN = 0.42` (update from 0.38)

## What Not To Do

- Full-frame `approxPolyDP` 6-gon contest
- Fixed isometric angle families (0°, 35°, 90°, 145°)
- Score without ROI `area_ratio`
- Re-spike — code exists in `block_spike_lib.py`

## Failure Analysis (17 images)

`dt2, dt40, dt53, dt54, dt56, dt60, dt63, dt64, dt70, dt80, dt86, dt90, dt95, dt98, dt104, dt105, dt107` — low edge_support (0.22–0.37), not ROI/fit failures.

## Validation Architecture

| Requirement | Test approach |
|-------------|---------------|
| SPIKE-ROI-* | Unit: ROI on dt50, dt1; mask non-empty |
| SPIKE-FIT-* | Unit: returns 6 points with valid topology |
| SPIKE-SCORE-* | Unit: label-sized contour scores < 0.42 |
| SPIKE-BENCH-* | Integration: run benchmark, accept_rate ≥ 0.80 |

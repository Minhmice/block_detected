---
spike: 004
name: dataset-benchmark
type: standard
validates: "Given dt1–dt108, when pipeline run, then overlays + error stats saved"
verdict: VALIDATED
related: [001, 002, 003]
tags: [benchmark, dataset, overlay]
---

# Spike 004: Dataset Benchmark

## What This Validates

Given full `block_dataset` (108 images), when end-to-end spike pipeline runs, then per-image overlays and aggregate JSON stats are produced for regression tracking.

## How to Run

```bash
.venv/bin/python .planning/spikes/004-dataset-benchmark/run.py
```

Outputs:
- `output/overlays/dt*_bench.jpg` — 108 overlay images
- `output/benchmark.json` — full results + failure list
- `output/forensic.json` — run metadata

## What to Expect

| Metric | Baseline (contour) | Spike pipeline |
|--------|-------------------|----------------|
| Detection rate | 27/108 (25%) | 91/108 (84%) |
| Avg hex area | ~3.5k (labels) | ~142k (cluster) |
| Avg score | 0.76 (misleading) | 0.61 |

## Failure Analysis (17 images)

Low edge-support scores on: `dt2, dt40, dt53–56, dt60, dt63–64, dt70, dt80, dt86, dt90` + 5 more.

Common pattern: weak Canny edges, heavy blur, or blocks far from camera. Scores 0.22–0.37 (below 0.42 threshold).

## Investigation Trail

1. Harness reuses `process_image()` from shared lib.
2. Compared against legacy `find_hexagons` baseline (25% hit rate).
3. Failures correlate with low contrast — not ROI/fit failures (0 fail_roi, 0 fail_fit).
4. Threshold tuning (0.38?) could recover ~5 frames at cost of 2–3 false accepts.

## Results

**Verdict: VALIDATED ✓**

- Benchmark harness works end-to-end
- 84% accept rate proves feasibility vs 25% baseline
- Failure list gives build-phase tuning targets

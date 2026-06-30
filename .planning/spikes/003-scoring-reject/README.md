---
spike: 003
name: scoring-reject
type: standard
validates: "Given candidates, when area/edge-support/topology scored, then labels/logos/pallet rejected"
verdict: VALIDATED
related: [001, 002, 004]
tags: [scoring, reject, topology]
---

# Spike 003: Scoring + Reject

## What This Validates

Given legacy contour candidates (small labels) and new ROI+fit candidates, when composite scoring runs, then small false positives are rejected and cluster-sized detections accepted.

## Research

Scoring formula (spike):

```
score = 0.35 * area_ratio + 0.45 * edge_support + 0.20 * topology_pass
reject if hex_area < 3500 or area_ratio < 0.12
accept threshold: 0.42
```

| Signal | Purpose |
|--------|---------|
| `area_ratio` | Hex area vs ROI — kills tiny labels |
| `edge_support` | Fraction of hex edges on Canny pixels |
| `topology` | A<B<C, F<E<D, row separation |

## How to Run

```bash
.venv/bin/python .planning/spikes/003-scoring-reject/run.py
```

## What to Expect

- Red = rejected legacy small contour
- Green = accepted new pipeline
- Orange = new candidate below threshold

## Investigation Trail

1. Legacy: 24/27 hits had area < 8000 (labels); score up to 0.97.
2. New scoring rejects area_ratio < 0.12 — blocks 21 legacy false-positive patterns.
3. Strict topology on E-row blocks 3 remaining edge cases.
4. 91/108 accepted (84%) vs legacy 27/108 (25%).

## Results

**Verdict: VALIDATED ✓**

- 91/108 accepted (84.3%)
- `legacy_small_contour_blocked`: 21 cases where old pipeline would pick label-sized contour
- Avg accepted hex area ~142k vs legacy ~3k

---
spike: 001
name: roi-silhouette
type: standard
validates: "Given full frame, when ROI extracted, then block cluster isolated from pallet/background with 3-block right trim"
verdict: VALIDATED
related: [002, 003, 004]
tags: [roi, silhouette, opencv, morphology]
---

# Spike 001: ROI / Silhouette

## What This Validates

Given a warehouse frame with blocks + pallet + background, when edge-cluster ROI runs with 3-block right trim, then a mask isolates the block cluster without requiring a closed 6-vertex contour.

## Research

| Approach | Tool | Pros | Cons | Status |
|----------|------|------|------|--------|
| Full-frame contour | `findContours` | Simple | Label/logo wins | Rejected (baseline bug) |
| Edge CC + morph close | OpenCV morphology | Fast, no ML | ROI can be loose | **Chosen** |
| Color segmentation | HSV white blocks | Tight on blocks | Lighting-sensitive | Deferred |

**Chosen:** Canny edges → mask bottom 22% (pallet) → morph close/dilate → largest upper CC → bbox with 22% right trim for 3-block mode.

## How to Run

```bash
.venv/bin/python .planning/spikes/001-roi-silhouette/run.py
.venv/bin/python .planning/spikes/001-roi-silhouette/run.py --image dt50.jpg --show
```

## What to Expect

- `output/*_roi.jpg` — orange ROI overlay per image
- `output/results.json` — per-image ROI boxes
- **108/108** images get a ROI mask (100%)

## Observability

`output/forensic.json` — event log with ROI dimensions per frame.

## Investigation Trail

1. Baseline contour picks label hexagons (area ~2.5k–4k) on 24/27 legacy hits.
2. Morph close (9×9) merges block-edge fragments; pallet strip mask removes floor edges.
3. Right trim (22%) enforces 3-block silhouette per requirement 2B.
4. ROI is sometimes loose (near full frame on wide clusters) — acceptable for spike; tighten in build phase.

## Results

**Verdict: VALIDATED ✓**

- 108/108 ROI found (100%)
- Isolates cluster well enough for downstream line fit + scoring
- 3-block right trim applied consistently

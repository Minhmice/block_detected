---
spike: 002
name: constrained-edge-fit
type: standard
validates: "Given Hough/LSD lines in ROI, when topology fit applied, then A–F recovered even if contour unclosed"
verdict: PARTIAL
related: [001, 003]
tags: [hough, topology, hexagon, lines]
---

# Spike 002: Constrained 6-Edge Fit

## What This Validates

Given 150+ Hough line segments in ROI, when topology-aware fitting runs, then A–F hexagon is produced without requiring a closed 6-vertex contour.

## Research

| Approach | Tool | Pros | Cons | Status |
|----------|------|------|------|--------|
| Fixed-angle families (0°,35°,90°,145°) | Hough | Pure geometry | **0/108** — angles cluster 14°–47° only | Invalidated |
| ROI-seed + line snap | Custom | Robust, uses lines | Not pure line intersection | **Chosen** |
| `approxPolyDP` contour | OpenCV | Fast | Fails on open/broken edges | Baseline bug |

**Chosen:** Seed A–F from ROI isometric proportions → dominant-angle line refinement → snap corners to edge pixels.

## How to Run

```bash
.venv/bin/python .planning/spikes/002-constrained-edge-fit/run.py
.venv/bin/python .planning/spikes/002-constrained-edge-fit/run.py --image dt50.jpg --show
```

## What to Expect

- Green hexagon overlay on block cluster
- 108/108 produce a hexagon (topology relaxed)
- Corners snap to nearest edge pixels within 12px

## Investigation Trail

1. **Pivot:** Strict isometric line families failed 108/108 — dataset lines peak at ~30° not 0°/90°.
2. Dominant-angle histogram finds real peaks per image.
3. ROI-seed guarantees topology; lines refine B/E/A/C when intersections exist.
4. Edge snap improves alignment on high-contrast block corners.

## Results

**Verdict: PARTIAL ⚠**

- 108/108 hexagons fitted (100%)
- Pure Hough→topology alone is **not sufficient** for this dataset
- ROI-seed + line assist **is** a viable build path
- Corner precision still rough on low-contrast frames (see spike 004 failures)

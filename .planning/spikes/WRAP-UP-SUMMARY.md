# Spike Wrap-Up Summary

**Date:** 2026-06-29  
**Spikes processed:** 4  
**Feature areas:** ROI/silhouette, hexagon fit, scoring/reject, benchmark harness  
**Skill output:** `.cursor/skills/spike-findings-block-detected/`

## Processed Spikes

| # | Name | Type | Verdict | Feature Area |
|---|------|------|---------|--------------|
| 001 | roi-silhouette | standard | VALIDATED ✓ | ROI / Silhouette |
| 002 | constrained-edge-fit | standard | PARTIAL ⚠ | Hexagon Fit |
| 003 | scoring-reject | standard | VALIDATED ✓ | Scoring & Reject |
| 004 | dataset-benchmark | standard | VALIDATED ✓ | Benchmark Harness |

## Key Findings

### Diagnosis confirmed
- Full-frame 6-vertex contour contest → label/logo wins (area ~2.5k–4k, score up to 0.97).
- 217 Hough lines/frame were computed but ignored in `main.py`.
- Legacy hit rate 27/108 (25%); 24/27 hits were small-area false positives.

### Proven pipeline (84% accept)
```
preprocess → Canny+Hough → ROI (morph CC, pallet mask, 3-block trim)
  → fit (ROI-seed + dominant-angle line refine + edge snap)
  → score (area_ratio + edge_support + topology)
```

### Dead ends
- Fixed-angle Hough families (0°/35°/90°/145°): 0/108
- Contour-only `approxPolyDP(6)`: label false positives
- Score without ROI area context: misleading high scores

### Build backlog
- 17 images fail on low `edge_support` (blur/distance) — not ROI/fit failures
- ROI sometimes loose; tighten with column analysis in build phase
- Spike 005 temporal stability deferred per user scope (1B)

## Skill Artifacts

| File | Purpose |
|------|---------|
| `.cursor/skills/spike-findings-block-detected/SKILL.md` | Auto-load index + requirements |
| `references/*.md` | Per-feature implementation blueprints |
| `sources/` | Original spike scripts for copy-paste |

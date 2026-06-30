# Spike Manifest

## Idea

Fix `block_detection_v2` classical-CV detection so it finds the real block cluster (A–F hexagon) instead of small label/logo contours. The current pipeline ignores Hough/LSD lines, scores without ROI context, and accepts loose topology. Spikes validate ROI isolation, constrained edge fitting, scoring/reject, and dataset benchmark before integrating into the main module.

## Requirements

- **Scope:** Spikes 001–004 only; temporal tracking (005) deferred.
- **Silhouette:** 3-block mode — hexagon wraps 3 front-facing blocks; exclude the outermost right block (not full 4-block front+right wrap).
- **Stack:** Python 3.10+, OpenCV, existing `block_detection_v2` preprocessing/edges as baseline.
- **Dataset:** `src/block_detection_v2/block_dataset/dt1.jpg`–`dt108.jpg` for benchmark spike.
- **Observable output:** Visual overlays + JSON forensic logs per spike.
- **Build path:** ROI-seed + line refinement + composite scoring (not contour-only, not fixed-angle Hough alone).

## Spikes

| # | Name | Type | Validates | Verdict | Tags |
|---|------|------|-----------|---------|------|
| 001 | roi-silhouette | standard | Given full frame, when ROI extracted, then block cluster isolated from pallet/background with 3-block right trim | VALIDATED ✓ | roi, silhouette, opencv |
| 002 | constrained-edge-fit | standard | Given Hough/LSD lines in ROI, when topology fit applied, then A–F recovered even if contour unclosed | PARTIAL ⚠ | hough, topology, hexagon |
| 003 | scoring-reject | standard | Given candidates, when area/edge-support/topology scored, then labels/logos/pallet rejected | VALIDATED ✓ | scoring, reject |
| 004 | dataset-benchmark | standard | Given dt1–dt108, when pipeline run, then overlays + error stats saved | VALIDATED ✓ | benchmark, dataset |

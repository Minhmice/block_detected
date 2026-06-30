# Spike Conventions

Patterns established across block_detection_v2 spike session (2026-06-29).

## Stack

- Python 3.10+ with project venv (`.venv/bin/python`)
- OpenCV 4.x — Canny, morphology, HoughLinesP, connected components
- Reuse `block_detection_v2.preprocessing` + `edges` modules

## Structure

```
.planning/spikes/
├── MANIFEST.md
├── CONVENTIONS.md
├── shared/block_spike_lib.py   # cross-spike pipeline
├── NNN-name/
│   ├── README.md
│   ├── run.py
│   └── output/
```

## Patterns

- **3-block silhouette:** ROI right-trim 22%; hex seed from ROI box not full 4-block wrap
- **Pipeline order:** preprocess → edges → ROI → masked edges → fit → score
- **Forensic logs:** JSON event arrays per spike in `output/forensic.json`
- **Visualization-first:** every spike writes `output/*_*.jpg` overlays

## Tools & Libraries

| Use | Choice |
|-----|--------|
| Edge detect | Existing `detect_edges()` (Canny + HoughLinesP) |
| ROI | Morph close 9×9 + largest CC + pallet mask |
| Fit | ROI-seed hex + dominant-angle line refine + edge snap |
| Score | area_ratio + edge_support + topology |
| Dataset | `src/block_detection_v2/block_dataset/dt*.jpg` |

## Avoid

- Full-frame `approxPolyDP` 6-gon contest (label wins)
- Fixed 0°/90° line families on this dataset
- Score without ROI area context

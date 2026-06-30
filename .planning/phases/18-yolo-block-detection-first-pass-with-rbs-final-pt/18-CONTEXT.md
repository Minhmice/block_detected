# Phase 18 Context

## Goal

YOLO detects LEGO blocks **first** using `models/rbs-final.pt`. Classical CV (edges → ROI/fit → score → hex A–F) runs on YOLO bbox ROI, not full-frame edge connected-components.

## Constraints (user)

- **New code only** in `block_detection_v2` — no v1 imports
- **Ultralytics YOLO** — simple wrapper in `yolo_detector.py`
- Model: `models/rbs-final.pt` (repo root, do not edit weights)
- Phase 17 hex formula + scoring stays; YOLO replaces primary ROI seed

## Locked decisions

| ID | Decision |
|----|----------|
| D-01 | `USE_YOLO_ROI=True` by default when wired |
| D-02 | `roi_from_bbox` applies same 3-block 22% right trim as edge ROI |
| D-03 | YOLO miss → fallback `extract_cluster_roi` (`stage=edge_roi`) |
| D-04 | One hex detection attempt per YOLO box (up to `MAX_BLOCKS`) |
| D-05 | Benchmark gate ≥80% accept unchanged |

## Canonical references

- `docs/BLOCK_DETECTION_V2.md` — v2 pipeline + YOLO section
- `src/block_detection_v2/yolo_detector.py` — Ultralytics wrapper (scaffolded)
- `src/block_detection_v2/pipeline.py` — integration target
- `models/rbs-final.pt` — weights (read-only)

## Delivered before execute

- `yolo_detector.py` — `YoloBlockDetector`, `YoloBlockBox`
- `docs/BLOCK_DETECTION_V2.md`

## Plans (4)

1. **18-01** — config + YOLO tests
2. **18-02** — `roi_from_bbox`
3. **18-03** — pipeline YOLO-first
4. **18-04** — main, benchmark, docs, gate

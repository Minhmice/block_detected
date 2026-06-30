# Phase 18 Research: YOLO block detection first pass

**Researched:** 2026-06-29
**Domain:** Ultralytics YOLO + classical CV ROI fusion

## RESEARCH COMPLETE

## Summary

Phase 18 adds a **YOLO first-pass** using `models/rbs-final.pt` (Ultralytics) before the Phase 17 classical pipeline. `yolo_detector.py` already exists as a thin wrapper — remaining work is ROI-from-bbox, pipeline orchestration, and benchmark parity.

## Key Findings

| Area | Decision | Rationale |
|------|----------|-----------|
| Model | `models/rbs-final.pt` | User-specified; smoke test on dt50 returns 2 boxes @ conf 0.91 |
| v1 code | **Do not import** | ISO-02 relaxed for YOLO only; new file stays in `block_detection_v2` |
| ROI source | YOLO bbox → `ROIBox` mask | Replaces edge-CC as **primary** seed; edge-CC when YOLO empty |
| Multi-box | One hex per YOLO box | Aligns with `MultiTracker` + `MAX_BLOCKS` |
| Coordinates | Hex fit in **full frame** | Crop for edges optional; map ROI mask in frame coords |
| Fallback | `extract_cluster_roi` unchanged | YOLO-04 requirement |

## Architecture

```
frame (BGR)
  → YoloBlockDetector.detect(frame)     # full frame
  → for each box (sorted by conf):
        roi = roi_from_bbox(box, shape)  # rectangular mask + 3-block trim
        detect_hex_in_roi(color, gray, roi)  # edges → fit → score
  → if no YOLO boxes: legacy edge-CC path (current detect_raw_hexagons body)
```

## `roi_from_bbox` design

```python
def roi_from_bbox(x1, y1, x2, y2, frame_shape, *, block_mode=3, pad_frac=0.05) -> ROIBox:
    # pad bbox, clamp to frame
    # apply BLOCK_MODE==3 right trim on bbox width (same 22% as edge ROI)
    # mask = filled rectangle (no edge CC)
```

Advantages: stable when pallet edges confuse Canny CC; localizes classical CV to block region.

Risks: YOLO miss → must fallback; YOLO box too tight → pad_frac + tune offsets in fit still apply.

## Config additions

```python
USE_YOLO_ROI = True
YOLO_MODEL_PATH = repo / "models" / "rbs-final.pt"
YOLO_CONF = 0.25
YOLO_IOU = 0.45
YOLO_PAD_FRAC = 0.08
YOLO_DEVICE = None  # auto
```

## What Not To Do

- Copy v1 `block_detected/detection/*`
- Run YOLO inside crop only (misses global context for multi-block)
- Remove edge-CC fallback
- Edit `models/rbs-final.pt`
- Break benchmark ≥80% gate

## Validation Architecture

| Requirement | Test approach |
|-------------|---------------|
| YOLO-01 | `test_yolo_detector_loads_model` — model path exists, detect returns list |
| YOLO-02 | `test_yolo_box_fields` — xyxy, conf, class_name on dt50 |
| YOLO-03 | `test_pipeline_yolo_roi_stage` — meta `stage=yolo_roi` when boxes found |
| YOLO-04 | `test_benchmark_accept_rate` still ≥0.80; fallback meta `stage=edge_roi` when YOLO mocked empty |

## Dependencies

- `ultralytics>=8.4.0` already in `pyproject.toml`
- Phase 17 `pipeline.py`, `roi.py`, `fit.py`, `score.py` unchanged in spirit

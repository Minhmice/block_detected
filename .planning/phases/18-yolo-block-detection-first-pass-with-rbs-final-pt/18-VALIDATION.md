---
phase: 18-yolo-block-detection-first-pass-with-rbs-final-pt
validation_targets:
  - YOLO-01
  - YOLO-02
  - YOLO-03
  - YOLO-04
---

# Phase 18 Validation Strategy

| REQ-ID | Dimension | Verification |
|--------|-----------|--------------|
| YOLO-01 | Unit | Model loads from `models/rbs-final.pt`; no v1 imports |
| YOLO-02 | Unit | `YoloBlockBox` fields + sorted detect on dt50 |
| YOLO-03 | Integration | Pipeline `stage=yolo_roi` when YOLO returns boxes |
| YOLO-04 | Regression | Benchmark accept_rate ≥ 0.80; edge_roi fallback when YOLO empty |

Test command: `PYTHONPATH=src pytest tests/test_block_detection_v2_yolo*.py tests/test_block_detection_v2_benchmark.py -q`

# 18-01 Summary

**Status:** Complete  
**Wave:** 1

## Delivered

- `config.py` — `USE_YOLO_ROI`, `YOLO_MODEL_PATH`, `YOLO_CONF`, `YOLO_IOU`, `YOLO_PAD_FRAC`, `DEBUG_YOLO`
- `yolo_detector.py` — defaults from config
- `tests/test_block_detection_v2_yolo.py`

## Verification

`pytest tests/test_block_detection_v2_yolo.py -q` — pass

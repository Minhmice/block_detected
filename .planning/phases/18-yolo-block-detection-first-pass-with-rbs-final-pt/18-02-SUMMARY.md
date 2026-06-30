# 18-02 Summary

**Status:** Complete  
**Wave:** 2

## Delivered

- `roi_from_bbox()` in `roi.py` — YOLO xyxy → rectangular `ROIBox` + 3-block trim
- `tests/test_block_detection_v2_yolo_roi.py`

## Verification

`pytest tests/test_block_detection_v2_yolo_roi.py -q` — pass

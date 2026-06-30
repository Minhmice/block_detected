# 17-01 Summary

**Status:** Complete  
**Wave:** 1

## Delivered

- `src/block_detection_v2/roi.py` — `extract_cluster_roi`, `ROIBox`
- Config: `BLOCK_MODE`, `ROI_PALLET_FRAC`, `ROI_RIGHT_TRIM_FRAC`
- `tests/test_block_detection_v2_roi.py` — 3 tests green

## Verification

`pytest tests/test_block_detection_v2_roi.py -q` — pass

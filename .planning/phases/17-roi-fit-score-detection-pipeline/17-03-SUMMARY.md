# 17-03 Summary

**Status:** Complete  
**Wave:** 3

## Delivered

- `src/block_detection_v2/score.py` — composite scoring + topology
- `src/block_detection_v2/pipeline.py` — ROI-fit-score path with optional contour fallback
- `config.py` — scoring weights, `DETECTION_SCORE_MIN=0.42`, `USE_CONTOUR_FALLBACK=False`
- `main.py` — primary path via `detect_raw_hexagons`
- `tests/test_block_detection_v2_score.py` — 4 tests green

## Verification

`process_frame` on dt50: detected=True, score≥0.42

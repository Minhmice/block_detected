# 03-01 Summary — Preprocess (GEO-01)

**Completed:** 2026-05-31

## Delivered

- `src/block_detected/preprocess.py` — `PreprocessSettings`, `PreprocessResult`, `preprocess_bgr`
- `config/vision.example.json` — preprocess defaults
- `tests/test_preprocess.py` — 6 tests

## Notes

- Default `adaptive_threshold_type` is `THRESH_BINARY_INV` so bright block faces on dark backgrounds yield isolated face masks (full-frame adaptive BINARY otherwise swamps the mask).

## Verify

```bash
python -m pytest tests/test_preprocess.py -q
```

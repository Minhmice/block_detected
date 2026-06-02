# Phase 6 — Verification

## Automated

```bash
.venv/bin/python -m pytest tests/ -q
```

Covers: IoU/area geometry, confidence/area/edge rejects, duplicate merge, temporal votes, `DetectionPostProcessor` pipeline.

## Manual (webcam)

- [ ] Enable stability in GUI; noisy detections reduce
- [ ] Raise min confidence / min area — small false positives drop
- [ ] Reject edge boxes removes partial boxes at frame border
- [ ] Temporal window + votes suppress single-frame flicker
- [ ] Save TOML → restart app → stability settings persist
- [ ] Overlay trail uses filtered boxes when stability on

# Phase 5 — Manual UAT checklist

Run on a machine with webcam access and at least one `models/*.pt` file.

## Setup

- [x] `pip install -e ".[dev]"` — **2026-06-07:** automated install verified
- [x] `block-detected` launches without import errors — **2026-06-07:** console script target verified in `tests/test_gui_optional.py`

## Missing model

- [ ] Temporarily rename `models/` or remove `.pt` files
- [ ] Start → error dialog mentions `models/` directory path
- [ ] Restore models and Start succeeds

## Camera

- [ ] Start with valid camera index → preview updates
- [ ] Set invalid camera index, Stop, Start → error mentions camera index
- [ ] Close other apps using camera if open fails

## Start / Stop

- [ ] Start → Stop → preview stops, status "Stopped"
- [ ] Rapid Start/Stop 5× — no crash; after Stop pending, Start stays disabled until worker exits
- [ ] Close window while running → camera released (no hung LED)

## Model / camera switch (while running)

- [ ] Next model cycles weights; failed load keeps previous model (check log)
- [ ] Next camera switches index when another device exists

## Hot config (no restart)

- [ ] Confidence slider changes detection threshold in preview
- [ ] Eval mode toggles eval drawing
- [ ] Overlay trail on/off and trail frame count
- [ ] Show FPS flag updates status bar in preview

## Restart-only fields

- [ ] While running: camera index/width/height/max, default model, log level disabled
- [ ] Editing restart field shows "Restart required…" hint
- [ ] Changed camera index applies only after Stop + Start

## Config file

- [ ] Save TOML writes `block_detected.toml`
- [ ] While running, saving camera/model changes shows "apply on next Start" message
- [ ] Restart app — saved values load

## Logs panel

- [ ] Log view updates without crash during inference
- [ ] No UI freeze when many log lines append

## Automated (CI / dev without camera)

- [x] `python -m pytest tests/ -q` passes — **2026-06-07:** 76 passed
- [x] Without PySide6: `_print_missing_qt()` returns 1 — **2026-06-07:** `tests/test_gui_optional.py`

**Agent note:** Manual items above were not executed in the headless agent environment (no camera permission). Automated hardening covered in `tests/test_gui_hardening.py`.

# Phase 5 Verification

**Status:** passed  
**Date:** 2026-06-07  
**Method:** Automated pytest; manual UAT optional

## Script Name Decision

**Choice:** Use existing `block-detected` console script (`pyproject.toml` → `block_detected.apps.gui.app:main`).  
No separate `block-detected-gui` alias added; UAT doc updated to match.

## Automated Evidence

```bash
python -m pytest tests/ -q
python -m pytest tests/test_gui_hardening.py -q
```

**Result:** 76 passed

| Hardening truth | Test / evidence | Status |
|-----------------|-----------------|--------|
| Stale `frame_ready` / `error` signals ignored | `test_stale_frame_ready_ignored`, `test_stale_worker_error_does_not_show_dialog` | passed |
| `frame_thread` not cleared until `_finalize_worker_stop` | `test_finalize_worker_stop_clears_thread_and_status`, `test_finalize_worker_stop_ignores_non_current_thread` | passed |
| Stop-pending disables Start | `test_stop_pending_disables_start` | passed |
| Restart hint while running | `test_restart_hint_when_camera_index_differs_while_running` | passed |
| `destroy_cv_windows=False` in FrameThread | source assertion in `test_frame_thread_shutdown_uses_destroy_cv_windows_false` | passed |
| Missing PySide6 exit path | `test_print_missing_qt_returns_nonzero` | passed |
| Save TOML apply-on-next-Start message | `_save_config` + `needs_runtime_restart` in `app.py` | passed (code) |

## Manual UAT (Optional)

Cross-reference `05-UAT.md` unchecked items — require webcam + models:

- [ ] Missing model error dialog mentions `models/` path
- [ ] Invalid camera index error on Start
- [ ] Rapid Start/Stop 5× — no crash; Start disabled while stop pending
- [ ] Close window while running — camera LED off
- [ ] Restart fields disabled while running; restart hint visible
- [ ] Save TOML while running with camera change → "apply on next Start"
- [ ] Log panel updates without freeze

**Autonomous mode:** Manual items documented as `human_needed`; not blocking closure.

## Plans

| Plan | Summary | Status |
|------|---------|--------|
| 05-01 | GUI hardening unit tests | complete |
| 05-02 | UAT alignment + verification doc | complete |

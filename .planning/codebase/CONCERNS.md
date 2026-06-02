# Codebase Concerns

**Analysis Date:** 2026-06-02

## Tech Debt

**Legacy config modules vs AppConfig:**
- Issue: `config/camera.py`, `inference.py`, `ui.py` duplicate defaults also defined via `AppConfig`
- Files: `src/block_detected/config/`, `runtime/config_schema.py`
- Impact: Drift if only one side updated
- Fix: Single source — generate legacy constants from `AppConfig.defaults()` or deprecate legacy modules

**Classical / stability config stubs:**
- Issue: `ClassicalPipelineConfig`, `StabilityConfig` exist but unused in engine
- Files: `runtime/config_schema.py`
- Impact: Confusing for readers
- Fix: Wire in future phase or document as reserved in AGENTS.md only

## Performance

**Eval mode copies full frame:**
- Issue: `frame.copy()` each frame in eval mode
- Files: `runtime/engine.py`
- Tradeoff: Needed for custom labels vs `plot()`; acceptable for debug mode

**Model reload on switch only:**
- Issue: `switch_model` loads new YOLO each time — correct behavior, but slow on large models
- Mitigation: Already avoids reload except on switch

## Fragile Areas

**OpenCV arrow key codes:**
- Issue: `KEY_ARROW_UP` / `DOWN` platform-specific in `config/ui.py`
- Files: `ui/input/handlers.py`
- Trigger: Different OS may need different codes

**Ultralytics `result.plot()` in normal mode:**
- Issue: Tied to Ultralytics rendering; harder to customize colors without reimplementing draw
- Files: `runtime/engine.py`
- Tradeoff: Kept for behavioral parity with original app

## Test Coverage Gaps

- No integration test for `WebcamEngine.process_frame`
- Risk: Regressions in render/eval branch
- Priority: Medium — add fake detector + numpy frame test later

## Dependencies

- Ultralytics + PyTorch stack is heavy; pinning versions not done in `requirements.txt`
- Risk: Breaking upstream changes
- Mitigation: Add CI + lockfile when project matures

## Security

- Local-only; no network secrets
- Do not commit `models/*.pt` or env files

---

*Concerns audit: 2026-06-02*

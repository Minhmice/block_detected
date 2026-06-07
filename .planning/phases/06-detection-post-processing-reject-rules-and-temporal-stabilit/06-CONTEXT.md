# Phase 6: Detection post-processing, reject rules, and temporal stability - Context

**Gathered:** 2026-06-07
**Status:** Ready for planning
**Mode:** Auto-generated (autonomous)

<domain>
## Phase Boundary

Post-inference filtering and temporal stability in `runtime/postprocess.py`: min confidence, min area, edge reject, duplicate merge IoU, temporal vote window. Wired into engine when `stability.enabled`. GUI/TOML controls.

</domain>

<decisions>
## Implementation Decisions

### Postprocess Pipeline
- `DetectionPostProcessor` applies filters then temporal votes
- Defaults: temporal_window=5, required_stable_votes=3 (Phase 9 will align to HTML spec)
- Tests in `tests/test_postprocess.py`

### Claude's Discretion
Retroactive closure — verify against 06-VERIFICATION.md, ensure tests cover all reject paths.

</decisions>

<code_context>
## Existing Code Insights

- `runtime/postprocess.py`, `vision/geometry.py`
- `tests/test_postprocess.py`
- `.planning/phases/06-.../06-VERIFICATION.md` — partial manual checklist

</code_context>

<specifics>
Mark verification passed when pytest covers automated criteria; note manual webcam items as human_needed optional.

</specifics>

<deferred>
top1_top2_margin, unknown class — Phase 9

</deferred>

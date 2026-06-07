# Phase 9: Stability and reject rules spec alignment - Context

**Gathered:** 2026-06-07
**Status:** Ready for planning
**Mode:** Auto-generated (autonomous)

<domain>
Align postprocess defaults with HTML spec; add top1_top2_margin, unknown_if_low_margin; web API for stability toggles.

</domain>

<decisions>
- Defaults: temporal_window=7, required_stable_votes=5, min_confidence=0.70
- Emit UNKNOWN class when margin too low
- Web API PATCH /api/config/stability

</decisions>

<code_context>
- runtime/postprocess.py, config_schema StabilityConfig
- html_data_requirements.md §5.3

</code_context>

<deferred>None</deferred>

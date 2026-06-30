# Phase 17: ROI-fit-score detection pipeline — Context

**Gathered:** 2026-06-29
**Status:** Ready for planning
**Source:** Spike session 001–004 + wrap-up (user decisions 1B, 2B)

<domain>
## Phase Boundary

Replace `block_detection_v2` contour-only detection (broken: label hexagons win) with spike-validated pipeline integrated into production modules. Scope: ROI extraction, line-assisted hex fit, composite scoring, benchmark harness. Temporal tracking improvements (spike 005) deferred.
</domain>

<decisions>
## Implementation Decisions

### Silhouette (D-01)
- **3-block mode** — hexagon wraps 3 front-facing blocks; exclude outermost right block
- ROI right trim ~22% of cluster bbox width

### Pipeline order (D-02)
- preprocess → detect_edges → extract_cluster_roi → masked edges → fit_hexagon_from_lines → score_candidate → tracker
- Hough lines MUST flow to fitter; stop discarding at `main.py:30`

### Fit strategy (D-03)
- ROI-seed A–F from isometric proportions on ROI box
- Refine with dominant-angle line histogram (NOT fixed 0°/90° families — invalidated 0/108)
- Snap corners to edge pixels within 12px

### Scoring (D-04)
- `score = 0.35*area_ratio + 0.45*edge_support + 0.20*topology`
- Hard reject: `hex_area < 3500` or `area_ratio < 0.12`
- Accept threshold: `0.42` (configurable `DETECTION_SCORE_MIN`)
- Strict topology on E-row at accept time

### Legacy path (D-05)
- Demote `find_hexagons()` / contour-primary to optional fallback only
- Keep `MultiTracker`, `renderer`, `geometry`, `image_source` unchanged where possible

### Benchmark (D-06)
- Port spike 004 harness into module (script or `benchmark.py`)
- Target: ≥80% accept on dt1–dt108 (spike achieved 84%)

### Claude's Discretion
- Exact module split (`roi.py`, `fit.py`, `score.py` vs extending existing files)
- Whether to keep contour fallback behind config flag
</decisions>

<canonical_refs>
## Canonical References

**Downstream agents MUST read these before planning or implementing.**

### Spike findings (primary)
- `.cursor/skills/spike-findings-block-detected/SKILL.md` — requirements + integration order
- `.cursor/skills/spike-findings-block-detected/references/roi-silhouette.md`
- `.cursor/skills/spike-findings-block-detected/references/hexagon-fit.md`
- `.cursor/skills/spike-findings-block-detected/references/scoring-reject.md`
- `.cursor/skills/spike-findings-block-detected/references/benchmark-harness.md`
- `.cursor/skills/spike-findings-block-detected/sources/shared/block_spike_lib.py` — proven spike code

### Current module
- `src/block_detection_v2/main.py` — pipeline entry, `_lines` discard bug
- `src/block_detection_v2/polygon.py` — legacy contour scoring
- `src/block_detection_v2/edges.py` — Canny + Hough
- `src/block_detection_v2/config.py` — thresholds

### Spike artifacts
- `.planning/spikes/WRAP-UP-SUMMARY.md`
- `.planning/spikes/004-dataset-benchmark/output/benchmark.json` — failure list
</canonical_refs>

<specifics>
## Specific Ideas

- Baseline bug: 27/108 detections, 24 were label-sized (area <8k, score up to 0.97)
- Spike pipeline: 91/108 accepted, avg hex area ~142k
- 17 known low-contrast failures — tune threshold later, not blocking v1 integration
</specifics>

<deferred>
## Deferred Ideas

- Spike 005 temporal stability across frames
- Tighter ROI via column analysis
- LSD vs Hough comparison
- YOLO ROI (existing TODO in main.py)
</deferred>

---

*Phase: 17-roi-fit-score-detection-pipeline*
*Context gathered: 2026-06-29 via spike wrap-up*

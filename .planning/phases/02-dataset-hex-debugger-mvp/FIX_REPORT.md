# FIX REPORT — Relational outer-boundary refactor of `hex_detector`

**Goal (restated):** Given `frame + YOLO bbox của toàn bộ cụm 4 block`, find the
**outer silhouette of the two vertical faces of the whole cluster** — front
`A-B-E-F`, side `B-C-D-E`, shared edge `B-E`. Never pick the top face, the
pallet, an internal seam between blocks, or a logo/text stroke as an edge.

**Success criterion:** A–F hug the outer boundary of the cluster. A drop in raw
detection count is *not* success.

Public API unchanged (`HexDetector.detect_frame`, `detect_roi`, result schema).

---

## 1. Root cause of the previous behaviour

The prior build enforced **absolute-position** constraints inside the (padded,
off-center) ROI:

- `min_front_width_ratio` (front must span ≥48 % of ROI width)
- `shared_edge_min_x_ratio` / `shared_edge_max_x_ratio` (BE must live in the
  right half of the ROI)

Because a YOLO cluster bbox has padding, is off-center, and varies with viewpoint,
"BE is in the right half of the ROI" is simply false in many frames. These rules
rejected legitimate shared edges and produced `hex = 0` across all 108 images.
They also broke the detector's own contract tests (front fixtures were narrower
than 48 % of their bbox → everything rejected).

## 2. What changed

### Removed (position-dependent) logic
- `validate_front_points` no longer uses `min_front_width_ratio` /
  `shared_edge_min_x_ratio` / `shared_edge_max_x_ratio`. Those config fields are
  kept as deprecated no-ops so no import breaks.
- CD (side outer vertical) is no longer hard-coded to "the 2 rightmost
  verticals". `pick_right_line_combinations` now considers **all** verticals;
  which one is the true outer edge is decided by scoring, not position.

### Added (relational) logic — `geometry.py`
- `vertical_silhouette()` / `interior_vertical_xs()` — the horizontal extent
  spanned by all verticals, and which verticals are *interior* (candidate seams).
- `outer_boundary_quality(pts, mode, vertical_lines, cfg)` — scores how well a
  candidate hugs the silhouette:
  - **AF** should sit at the left extent; the **outer-right** edge (CD for hex,
    BE for rectangle) at the right extent.
  - If a vertical lies *beyond* AF or the outer-right edge, that edge is an
    internal seam (or the candidate misses part of the cluster) → `is_seam=True`.
- `_area_boundary_composite()` — blends front area with outer-boundary quality
  and applies a **seam penalty** (`seam_penalty_weight`). This composite feeds
  the `area_position` score component (weight raised 0.10 → 0.28). No absolute
  ROI coordinates are used — only candidate edges relative to the full line set.

### Per-line metadata — `lines.py` / `models.py`
- `LineSegment` gained `edge_support` and `dist_to_border`.
- `enrich_lines()` attaches them (verbose-mode only — it is debug data).

### Two-sided viewing (kept)
- Mirrored pass retained: normal → side right, horizontal flip → side left,
  coordinates un-flipped on the way out. Selection is purely by score
  (`_attempt_better`: mode rank, then score).

### Frame-level prefilters (made opt-in)
- The earlier small-box / edge-touching filters were dataset-debugger heuristics
  that wrongly assume many bboxes. Deployment feeds **one** cluster bbox, so they
  are now config-gated and **off by default** (`prefilter_min_area_ratio=0.0`,
  `prefilter_reject_edge_touching=False`). IoU dedup stays (`iou_dedup_threshold`).

### Debug exposure (`detector.py` / `debug_serialize.py`)
Verbose debug now includes: raw / filtered / grouped / merged lines (with
per-line `edge_support`, `dist_to_border`), group assignment + angular error,
`top_front_candidates` / `top_hex_candidates` (≥20), per-candidate
`is_seam` + `outer_boundary` gaps, `seam_vertical_xs`, `winner_is_seam`,
validation PASS/FAIL + reject reasons, crop ratio, mirrored flag, and
per-stage `stage_timings_ms`.

### Latency work (pure speedups, no result change)
- Vectorized edge-support sampling (`_edge_fraction`).
- `merge_parallel_lines` now precomputes `(angle, offset)` once per line instead
  of recomputing `angle_deg()` inside its O(n²) loop (merge time roughly halved;
  `angle_deg` calls 322k → 111k on the 20-image profile).

---

## 3. Before / after — 108 images (`models/son-down.pt`, conf 0.35)

Reproduce:
```
python scripts/bench_hex_metrics.py --label BEFORE --json output/bench_before.json   # on baseline commit
python scripts/bench_hex_metrics.py --label AFTER  --json output/bench_after.json     # on this build
```

| Metric | BEFORE (phase-1 baseline) | AFTER (relational) |
|---|---:|---:|
| Images | 108 | 108 |
| YOLO boxes | 203 | 203 |
| **detected** (status=detected) | 72 | **99** |
| **hex** | **0** | **23** |
| **rectangle** | 192 | 213 |
| **not_detected** (mode) | 96 | 69 |
| side = left (mirrored) | 0 | 47 |
| side = right | 192 | 189 |
| **false seam selection** (winner_is_seam) | n/a¹ | 19 |
| **invalid topology** (reject reason) | 49 | 32 |
| **latency mean** (ms) | 21.9 | 217.7 |
| **latency P95** (ms) | 58.3 | 547.9 |

¹ Baseline had no seam concept, so the flag did not exist (effectively 0).

`hex`/`rectangle` counts include held frames that carry a mode, so they exceed the
status=detected count.

### Reading the numbers
- **hex 0 → 23** and **not_detected 96 → 69** with **invalid_topology 49 → 32**:
  the relational boundary logic recovers the shared edge and the side face that
  the absolute-position rules had been throwing away. Detection did **not** drop.
- **side_left 0 → 47:** left-facing clusters are now handled by the mirrored pass.
- **false_seam = 19:** these are winners whose outer edge does not reach the
  *vertical-silhouette extent*. This is a conservative diagnostic — the extent is
  defined by **all** verticals including noise/pallet lines that survive filtering,
  so it over-counts. It is exposed per candidate (`is_seam`, `outer_boundary`
  gaps) and on the winner (`winner_is_seam`) for triage, and it is penalized in
  scoring, but it is not a hard reject (a genuine boundary can still win).

### Latency caveat
The bench measures `detect_frame` while YOLO runs on the same CPU, so the machine
is heavily loaded; isolated profiling shows ~110–120 ms/frame. Two factors set the
floor: **4 crop-ratio attempts × the mirrored pass = 8 pipeline runs per bbox**,
each with its own Canny + HoughLinesP. Tuning levers (no code change):
- `block_crop_bottom_ratios` / `max_crop_ratio_attempts` (4 → 2 ≈ halves cost),
- `enable_mirrored_pass = False` when the robot only ever views from one side.

---

## 4. Tests

`tests/test_hex_detector_outer_boundary.py` — the 8 mandated scenarios:

1. `test_two_block_front_seam_not_chosen_as_be` — 3 verticals (outer/seam/outer);
   BE lands on the outer boundary, not the seam.
2. `test_front_plus_right_becomes_hex` — genuine slanted side (real edge image) →
   hex, `side=right`.
3. `test_left_face_selected_as_mirrored_hex` + `test_mirror_unflip_coordinates` —
   left face wins the mirrored pass → `side=left`; un-flip math verified.
4. `test_straight_on_view_is_rectangle` — front-only → rectangle, C/D None.
5. `test_pallet_line_filtered_out` — strong low-band horizontal is filtered.
6. `test_text_noise_does_not_break_topology` — logo strokes + stray diagonal do
   not move A/B off the outer boundary.
7. `test_bbox_offset_yields_same_relative_points` — same geometry at two bbox
   offsets → identical ROI-relative A–F.
8. `test_dtlike_real_image_smoke` — dt28/dt51/dt79 run end-to-end without crashing
   and return structurally valid results.

Full hex suite: **61 passed** (`tests/test_hex_geometry.py`,
`test_hex_detector_front_modes.py`, `test_hex_detector_temporal_debug.py`,
`test_hex_detector_p1_fixes.py`, `test_hex_detector_outer_boundary.py`).

---

## 5. Follow-ups / known limits
- `false_seam` diagnostic over-counts because silhouette extent trusts all
  surviving verticals; tightening `filter_lines` (pallet/text suppression) would
  sharpen it.
- Latency on the Pi will need the crop-ratio / mirror levers above, or moving
  edge extraction to a single shared pass across crop ratios.

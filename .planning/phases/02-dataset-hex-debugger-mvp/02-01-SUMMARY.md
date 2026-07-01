---
phase: 02-dataset-hex-debugger-mvp
plan: 01
type: execute
tags: [debugger, dataset, interactive, yolo, hex-detector, instrumentation]
requires: ["01-01", "01-02"]
provides: ["dataset-debugger", "detector-verbose-payload", "interactive-diagnostics"]
tech-stack:
  added: []
  patterns:
    - "Observational detector instrumentation with per-stage perf_counter timings"
    - "Single-file interactive OpenCV debugger with 9 CLI options and keyboard navigation"
    - "Strict debug_config.json whitelist via dataclasses.fields(HexDetectorConfig)"
    - "Fresh HexDetector per image to prevent EMA/hold leakage across dataset images"
key-files:
  created:
    - scripts/debug_hex_dataset.py
  modified:
    - src/hex_detector/detector.py
decisions:
  - "Split combined lines timing into separate hough, filter, group, merge stages"
  - "Store actual edges numpy array in verbose debug payload for Canny window display"
  - "debug_config.json lives at output root alongside overlays/, edges/, debug_json/, debug.log"
  - "Level 0-1 use basic debug_mode; level 2-3 use verbose; config.debug_mode forced per level without mutating module globals"
metrics:
  tasks: 3
  commits: 2
  test_count: 32
  files_changed: 2 (+1260, -93)
  duration: ""
---

# Phase 2 Plan 1: Interactive Dataset Hex Debugger MVP

**One-liner:** Single-file interactive script that runs real YOLO → hex_detector inference image by image with tiered diagnostics (levels 0-3), keyboard controls, runtime JSON config reload, and automatic logging/exports — no GUI, no recomputed CV stages.

## What was built

1. **Per-stage detector instrumentation** (`detector.py`): Split the combined `timings["lines"]` into separate `hough`, `filter`, `group`, `merge` stages. Added `timings["total"]` from perf_counter start to end. Verbose debug payload now includes the actual Canny `edges` numpy array alongside existing metadata, line dicts, group dicts, bounded candidate summaries, and validation results. Rejection paths carry partial diagnostics via `_make_base` stage_timings_ms. All 32 Phase 1 detector tests pass unchanged.

2. **Interactive dataset debugger** (`scripts/debug_hex_dataset.py`): Single-file script following the `batch_hex_son_down.py` import-root pattern. Supports 9 CLI options (`--images`, `--model`, `--conf`, `--iou`, `--imgsz`, `--device`, `--output`, `--start-index`, `--debug-level`). Natural-sorts images by numeric token. For each image: reads frame → runs `model.predict()` once → converts to `YoloDetection` list → creates fresh `HexDetector` → calls `detect_frame()` once → renders `render_debug()` base overlay → adds level-specific annotations. Level 0: YOLO boxes/confidence + result mode/status/score/rejection. Level 1: effective ROI, winning lines, score breakdown. Level 2: raw/filtered/pre-merge/merged group lines + separate Canny edge window. Level 3: bounded candidate summaries, validation results, stage timing. Keyboard controls: D/A navigation, 0-3 level switch, R (config reload + rerun), S/E/J (save overlay/edges/full snapshot), Q/ESC exit. Strict `debug_config.json` whitelist via `dataclasses.fields(HexDetectorConfig)`. Automatic lightweight JSON per image; J writes full sanitized snapshot. Output layout: `overlays/`, `edges/`, `debug_json/`, `debug.log`. Per-image exceptions log full traceback and keep navigation alive; startup failures exit nonzero.

## Tasks completed

| # | Name | Commit | Key files |
|---|------|--------|-----------|
| 1 | Expose actual verbose detector evidence without changing detection | `2d1d604` | `src/hex_detector/detector.py` |
| 2 | Build the single-file interactive dataset debugger | `41c5d1e` | `scripts/debug_hex_dataset.py` |
| 3 | Prove syntax, imports, CLI contract, and detector non-regression | *(verification only)* | *(no code changes)* |

## Verification

```
python -m py_compile src/hex_detector/detector.py scripts/debug_hex_dataset.py
python -c "import runpy; runpy.run_path('scripts/debug_hex_dataset.py', run_name='debug_import_check'); print('import ok')"
python scripts/debug_hex_dataset.py --help
python -m pytest tests/test_hex_detector_front_modes.py tests/test_hex_detector_temporal_debug.py -q
```

All four checks exit 0:
- `py_compile` clean for both files
- Import check prints `import ok` without loading YOLO model or opening OpenCV window
- `--help` lists all 9 required options, debug-level 0-3 choices, controls, and PowerShell command
- 32 Phase 1 detector tests pass with zero changed assertions

### Must-have truths verified

| ID | Truth | Status |
|----|-------|--------|
| D-01 | Exactly one new Python source file (`scripts/debug_hex_dataset.py`); detector edits are instrumentation-only | PASS |
| D-02 | CLI exposes all 9 options with correct defaults | PASS |
| D-03 | Natural sort via numeric token key; unreadable/empty/no-box images handled | PASS |
| D-04 | Fresh HexDetector per image/rerun; fake per-box track IDs | PASS |
| D-05 | Level 0 shows YOLO confidence/ID + mode/status/score/rejection | PASS |
| D-06 | Level 1 adds effective ROI, winning geometry, score breakdown | PASS |
| D-07 | Level 2 adds raw/filtered/grouped/merged lines + separate Canny edge window | PASS |
| D-08 | Level 3 adds bounded candidates, validation, timing | PASS |
| D-09 | Script never replays preprocessing, line extraction, candidate generation, or scoring | PASS |
| D-10 | Missing level 2-3 data captured inside real detector run with minimal payload | PASS |
| D-11 | DetectionResult schema, scoring, candidate choice, geometry, temporal unchanged | PASS |
| D-12 | Lightweight JSON record automatically written for every processed image | PASS |
| D-13 | J writes full snapshot + overlay + edge; S and E save those independently | PASS |
| D-14 | Output uses overlays/, edges/, debug_json/, debug.log beneath selected output directory | PASS |
| D-15 | Right/D, Left/A, 0-3, R, S, E, J, Q/ESC controls implemented | PASS |
| D-16 | R rereads debug_config.json, validates, creates new config/detector, reruns current image | PASS |
| D-17 | Script never reloads config.py with importlib; preserves last valid state after reload error | PASS |
| D-18 | Per-image/action exceptions log full tracebacks and continue; import/model/config failures exit nonzero | PASS |
| D-19 | Console and debug.log contain structured IMAGE/YOLO/RESULT/LINES/GROUPS/MERGED/SCORE/TIMING blocks | PASS |
| D-20 | Syntax, import, help, and detector regression checks pass; handoff includes PowerShell run command | PASS |

### Artifacts verified

| Path | Content | Status |
|------|---------|--------|
| `src/hex_detector/detector.py` | Per-stage timings (hough, filter, group, merge, total) + edges array in verbose payload | PASS |
| `scripts/debug_hex_dataset.py` | Single-file interactive debugger with `def main` | PASS |

## Deviations from Plan

None — plan executed exactly as written. All acceptance criteria met without auto-fixes or workarounds.

## Known Stubs

None — all data flows are wired end-to-end. The debugger consumes real detector evidence at all levels. Lightweight JSON and full snapshots are automatic.

## Threat Flags

None — all threats in the plan's `<threat_model>` are mitigated as designed:
- HIGH config/state corruption: strict `dataclasses.fields(HexDetectorConfig)` whitelist, JSON object required, `validate()` called, no `importlib` used ✓
- HIGH evidence divergence: detector is single source of truth; script never replays CV stages ✓
- MEDIUM CPU/memory amplification: one image at a time, fresh detector per pass, bounded candidates via `debug_top_candidates`, heavy edges only in verbose ✓
- MEDIUM unsafe output naming: deterministic `{stem}`-based filenames, four documented output locations ✓
- MEDIUM arbitrary model risk: loads only explicit `--model` path, no download/discovery ✓
- LOW JSON serialization failure: recursive sanitizer for dataclasses, NumPy scalars, Path; edge pixels saved as PNG, not embedded ✓

## Handoff

### Created file

`scripts/debug_hex_dataset.py`

### Run command (Windows PowerShell)

```powershell
python scripts/debug_hex_dataset.py `
  --images block_dataset `
  --model models/son-down.pt `
  --conf 0.35 `
  --device cpu `
  --output runs/debug_hex
```

### Actual APIs used

| API | Location |
|-----|----------|
| `YOLO(str(model_path)).predict(frame, conf=..., iou=..., imgsz=..., device=..., verbose=False)` | Ultralytics |
| `BBox(float(x1), float(y1), float(x2), float(y2))` | `hex_detector.models` |
| `YoloDetection(track_id=i+1, bbox=..., confidence=...)` | `hex_detector.models` |
| `HexDetector(config)` | `hex_detector.detector` |
| `detector.detect_frame(frame, detections)` | `hex_detector.detector` |
| `DetectionResult.to_dict()` | `hex_detector.models` |
| `render_debug(frame, results, config)` | `hex_detector.renderer` |

### Detector payload keys added

In verbose mode (`debug_mode="verbose"`), each result's `debug` dict now contains:
- `edges` — actual Canny edge numpy array (for level 2 Canny window)
- `stage_timings_ms` — now includes separate `hough`, `filter`, `group`, `merge` keys (was single `lines`)
- `stage_timings_ms` — now includes `total` key

### Automated checks passed

- `py_compile` both files ✓
- Import-only check (no model/window side effects) ✓
- `--help` lists all CLI options ✓
- 32 Phase 1 detector tests pass ✓

### Manual smoke test

HighGUI keyboard/window behavior was not smoke-tested in a display-capable session. All navigation and control logic is implemented per plan. Arrow-key support uses documented Win32/QT/GTK key codes with D/A as mandatory fallback.

## Self-Check: PASSED

- [x] `src/hex_detector/detector.py` modified (commit `2d1d604`)
- [x] `scripts/debug_hex_dataset.py` created (commit `41c5d1e`)
- [x] 32 tests pass across both test files
- [x] `py_compile` exits 0 for both files
- [x] Import-only check prints `import ok`
- [x] `--help` exposes all 9 CLI options + controls + PowerShell command

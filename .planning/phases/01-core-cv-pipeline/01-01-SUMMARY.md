# Plan 01-01: Typed front-first rectangle detection with optional hex upgrade

**Status:** Complete ✓
**Commits:** 2

## What was built

Front-first detection pipeline that replaces the old 7-line combinatorial bottleneck with independent rectangle-then-hex-optional logic. Rectangle (A-B-E-F) requires only 2 vertical + 2 front-horizontal lines; hex upgrades only when a validated right face (B-C-D-E) is supported by CD/BC/ED lines. C and D are never synthesized — they stay `None` when right-face evidence is absent.

## Files changed

| File | Change |
|------|--------|
| `src/hex_detector/models.py` | Added `ScoreBreakdown` dataclass, `DetectionStatus`/`RejectReason` string enums, `HexResult` alias |
| `src/hex_detector/config.py` | Added `max_front_candidates`, `max_right_candidates`, `min_edge_support_score` with validation |
| `src/hex_detector/lines.py` | `pick_front_line_combinations()` (2 vert + 2 fh), `pick_right_line_combinations()` (cd+bc+ed), reserves rightmost vertical for hex |
| `src/hex_detector/geometry.py` | `points_from_front_lines()`, `validate_front_points()`, `score_front_candidate()`, `score_hex_candidate()` all return `ScoreBreakdown`, topology_score uses active config |
| `src/hex_detector/detector.py` | Front-first `detect_roi()` → choose best rectangle → optionally upgrade to hex. All exits mapped to stable `RejectReason` codes |
| `src/hex_detector/__init__.py` | Exports `ScoreBreakdown`, `DetectionStatus`, `RejectReason`, `HexResult` |
| `tests/test_hex_detector_front_modes.py` | 8 deterministic tests covering rectangle, hex, no_front, no_lines, empty_roi, candidate caps, and public API |

## Key decisions

- **Front-first architecture**: Detect rectangle first from minimal 2-vertical + 2-horizontal lines; hex upgrade is additive, never destructive to front.
- **Bounded candidates**: `max_front_candidates` and `max_right_candidates` in config cap combinatorial generation — replaces the old single-7-line bottleneck.
- **Stable rejection codes**: `NO_LINES`, `NO_FRONT_FACE`, `INVALID_TOPOLOGY`, `LOW_EDGE_SUPPORT`, `LOW_SCORE`, `ROI_EMPTY` — each exit path in `detect_roi()` maps exactly one code.
- **Rightmost vertical preservation**: When 3+ verticals exist, the rightmost is reserved for hex CD edge rather than competing with middle verticals.

## Verification

```
python -m pytest tests/test_hex_detector_front_modes.py -q
8 passed
```

All must-have truths (D-01 through D-11) verified in code:
- D-01/D-02/D-03: Rectangle without right-face support, C/D `None` ✓
- D-08/D-09: Public `detect_frame(Sequence[YoloDetection])` delegates to `detect_roi()` ✓
- D-10: Float coordinates throughout, int only at render boundary ✓
- D-11: Stable machine-readable RejectReason codes ✓

## Self-Check: PASSED

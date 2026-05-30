# Architecture Research

**Domain:** Edge vision pipeline for cube block pick
**Researched:** 2026-05-31
**Confidence:** HIGH

## Standard Architecture

### System Overview

```
┌─────────────────────────────────────────────────────────────┐
│                     detect_block(frame)                      │
├─────────────────────────────────────────────────────────────┤
│  CameraCapture │ Preprocessor │ SquareDetector │ Classifier │
│       ↓              ↓              ↓               ↓       │
│   raw debug     thresh debug   corners+warp    block_id    │
├─────────────────────────────────────────────────────────────┤
│  GeometrySolver │ PoseMapper │ RejectPolicy │ Contract I/O  │
└─────────────────────────────────────────────────────────────┘
         calibration.yaml / homography.npy / model.tflite
```

### Component Responsibilities

| Component | Responsibility | Typical Implementation |
|-----------|----------------|------------------------|
| `detection_contract` | Types + validation | **Exists** — `detection_contract.py` |
| `camera` | Frame acquisition, exposure lock, save raw | `picamera2` or `VideoCapture` adapter |
| `preprocess` | BGR→binary/edges for contours | OpenCV ops, parameterized |
| `detector` | Contour → quad candidates | `findContours`, `approxPolyDP`, filters |
| `geometry` | Order corners, warp, center, angle | `order_points`, `getPerspectiveTransform` |
| `classifier` | Warped 128² → class + score | TFLite interpreter |
| `pose` | px → mm, theta for arm | Homography + offsets |
| `pipeline` | Orchestrate + map to `DetectionResult` | Single entry `detect_block` |
| `eval` | Offline metrics on test set | pytest + CSV reports |

## Recommended Project Structure

```
block_detected/
├── detection_contract.py      # existing contract
├── pyproject.toml or requirements.txt
├── src/
│   └── block_detected/
│       ├── __init__.py
│       ├── pipeline.py          # detect_block()
│       ├── camera.py
│       ├── preprocess.py
│       ├── detector.py
│       ├── geometry.py
│       ├── classifier.py
│       ├── pose.py
│       ├── reject.py
│       └── debug.py
├── models/
│   └── block_classifier_int8.tflite
├── config/
│   ├── camera.yaml
│   └── calibration.json
├── data/
│   ├── raw/
│   ├── warped/
│   └── labels.csv
├── scripts/
│   ├── capture_dataset.py
│   ├── train_export_tflite.py
│   └── run_eval.py
└── tests/
    ├── test_contract.py
    ├── test_geometry.py
    └── test_pipeline_smoke.py
```

### Structure Rationale

- **`src/block_detected/`:** Importable package for robot integration
- **`models/`:** Versioned TFLite artifact separate from code
- **`config/`:** Calibration and camera without code changes
- **`data/`:** Training and eval sets grow independently

## Architectural Patterns

### Pattern 1: Pure stages with debug artifacts

**What:** Each stage returns both result and optional debug image dict.

**When to use:** Always — field tuning requires visibility.

**Trade-offs:** Slightly more I/O; invaluable for threshold tuning.

### Pattern 2: Contract-first outputs

**What:** Internal structs convert to `DetectionResult` only at boundary.

**When to use:** Every public API return.

**Trade-offs:** Extra mapping code; prevents robot integration bugs.

### Pattern 3: Fail-safe reject policy

**What:** Central `RejectPolicy` scores geometry + classification before `status=ok`.

**When to use:** Before populating `pickup_pose`.

**Trade-offs:** May increase false rejects; safer for robot.

## Data Flow

```
Frame BGR (640×480)
  → preprocess → binary/edge map
  → contours → list[QuadCandidate]
  → pick best / reject multiple
  → order corners → warp 128×128
  → TFLite → (block_id, cls_conf)
  → geometry metrics → square_confidence
  → pose mapper (if calibrated) → PickupPose
  → RejectPolicy → DetectionResult + debug frames
```

## Build Order (dependencies)

1. Contract tests (exists)
2. Camera + debug save
3. Preprocess + contour detector (no ML)
4. Corner order + warp (unit tests with synthetic quads)
5. Dataset capture + CNN train/export
6. Classifier integration
7. Calibration + pose
8. Reject policy + full pipeline
9. Eval harness on real test set

## Anti-Patterns

### Anti-Pattern 1: Classify before warp

**What people do:** CNN on full frame crop by bbox.

**Why it's wrong:** Viewpoint and scale vary; 4-class confusions rise.

**Do this instead:** Warp square face first, then classify 128×128.

### Anti-Pattern 2: Unordered corners

**What people do:** Use `approxPolyDP` points in arbitrary order.

**Why it's wrong:** `warpPerspective` flips or rotates face → wrong class.

**Do this instead:** Sum/diff or angle-based `order_points` (TL, TR, BR, BL).

## Integration Points

| Boundary | Communication | Notes |
|----------|---------------|-------|
| Vision → Robot | JSON `result_to_json()` | Already in contract module |
| Train PC → Pi | Copy `model.tflite` + labels | Version model in filename |
| Calibration → Pose | JSON/YAML matrices | Invalid cal → `pickup_pose=None` |

## Sources

- LearnOpenCV document scanner pipeline — perspective transform pattern
- PyImageSearch four-point ordering — corner consistency
- Existing `detection_contract.py` in repo

---
*Architecture research for: block_detected*
*Researched: 2026-05-31*

# Phase 3: Core API & Contracts - Context

**Gathered:** 2026-07-03
**Status:** Ready for planning

<domain>
## Phase Boundary

Phase 3 delivers the greenfield package skeleton under `src/detect_only_v4/` with typed contracts (`DetectionResult`, protocols, errors), structured logging, and a working `inspect_model()` with authoritative family/task identification. Public API surface is declared; non-inspect functions are typed stubs raising `NotImplementedError` until later phases.

Out of scope for Phase 3: model loading beyond inspect, task adapters, camera backends, pipeline, Web UI.
</domain>

<decisions>
## Implementation Decisions

### DetectionResult schema
- **D-01:** `DetectionResult` fields: `class_id`, `class_name`, `confidence`, `xyxy` (4 floats), `center_x`, `center_y`, `width`, `height`, `track_id=None`, optional `mask`, `keypoints`, `obb_points`, `angle`.
- **D-02:** `mask` = list of polygon rings as `list[list[list[float]]]` — each ring is `[[x,y], ...]` JSON-safe floats; no raw ndarray on wire.
- **D-03:** `keypoints` = `list[dict]` with keys `x`, `y`, `conf` (float).
- **D-04:** `obb_points` = 4 corner pairs `[[x,y], ...]`; `angle` = float degrees; both optional, populated only for OBB task.
- **D-05:** `track_id` always `None` in v2.0 — no tracker integration.

### inspect_model identification chain
- **D-06:** Resolution order (stop at first confident result): (1) `YOLO(path).task` + checkpoint metadata after lightweight init for loadable paths; (2) `metadata.yaml` in NCNN/OpenVINO export directories; (3) filename heuristics as hints only (`yolo26*`, `yolo11*`, `yolov8*`, `-seg`, `-pose`, `-obb`); (4) single dry inference on dummy 640×640 zeros frame, inspect output tensor keys; (5) return `unknown` for family/task if still ambiguous — never guess.
- **D-07:** `inspect_model` returns `ModelInfo` dataclass: `path`, `format`, `family`, `task`, `class_names`, `imgsz`, `stride`, `loadable`, `error`, `identify_steps` (list of steps taken), `timing_ms` dict.
- **D-08:** `.engine` on Pi: `loadable=False`, `error` explains CUDA/TensorRT required — still inspectable for format discovery.

### Phase 3 scope (full vs stub)
- **D-09:** **Full implementation:** `core/types.py`, `core/protocols.py`, `core/errors.py`, `core/logging.py`, `models/inspector.py`, package `__init__.py` exports, `pyproject.toml` package entry if missing.
- **D-10:** **Stub only (signature + NotImplementedError):** `load_model`, `detect_frame`, `discover_cameras`, `probe_camera`, `normalize_results`, `draw_overlay` — each in dedicated module with docstring referencing target phase.
- **D-11:** `inspect_model` is the only function that may import/invoke Ultralytics in Phase 3.

### Enums and serialization
- **D-12:** `TaskKind` StrEnum: `detect`, `segment`, `pose`, `obb`, `unknown`.
- **D-13:** `ModelFamily` StrEnum: `yolov8`, `yolo11`, `yolo26`, `unknown`.
- **D-14:** `ModelFormat` StrEnum: `pt`, `onnx`, `engine`, `tflite`, `ncnn`, `openvino`, `unknown`.
- **D-15:** All dataclasses expose `to_dict()` → JSON-serializable plain strings for enums.

### Logging
- **D-16:** stdlib logging; root logger name `detect_only_v4`.
- **D-17:** Levels: INFO for inspect start/complete and loadable verdict; DEBUG per identification step; WARNING when falling back to dry infer or filename hint; ERROR on inspect failure.
- **D-18:** `inspect_model` records `timing_ms`: `init`, `metadata`, `dry_infer`, `total`.

### Greenfield constraint
- **D-19:** Zero imports from `hex_detector`, `block_detected`, `block_detected_v1`, `view`, `stream`, or any legacy module.

### Claude's Discretion
- Exact dummy frame size for dry infer (640 default aligned with YOLO).
- Whether `inspect_model` caches YOLO instance per path within call only (no global cache in Phase 3).
- Test fixture strategy for inspect without real weights in CI.

</decisions>

<canonical_refs>
## Canonical References

**Downstream agents MUST read these before planning or implementing.**

### Milestone planning
- `.planning/PROJECT.md` — v2.0 scope, greenfield rule, API names
- `.planning/REQUIREMENTS.md` — CORE-01 through CORE-06
- `.planning/ROADMAP.md` — Phase 3 deliverables and success criteria
- `.planning/research/SUMMARY.md` — architecture and pitfall summary
- `.planning/research/PITFALLS.md` — no task guessing (Pitfall 2)
- `.planning/research/ARCHITECTURE.md` — recommended `src/detect_only_v4/` layout

### External
- [Ultralytics Predict docs](https://docs.ultralytics.com/modes/predict/) — Results fields per task
- [Ultralytics model export](https://docs.ultralytics.com/modes/export/) — metadata.yaml convention

</canonical_refs>

<code_context>
## Existing Code Insights

### Reusable Assets
- None imported — greenfield module per D-19.

### Established Patterns
- Prior v1.0 `hex_detector` used dataclass contracts and typed reject reasons — mirror dataclass + enum style only, not code.

### Integration Points
- `models/` at repo root scanned by path only (no code dependency).
- `pyproject.toml` may need `[project]` package include for `detect_only_v4`.

</code_context>

<specifics>
## Specific Ideas

- User milestone spec: folder `src/detect_only_v4/`, no reading other project code during implementation.
- Identification must not guess — `unknown` is valid and preferred over wrong adapter.
- Vietnamese project context; code/comments in English per repo convention.

</specifics>

<deferred>
## Deferred Ideas

- `load_model` NCNN priority — Phase 4
- Task adapters — Phase 5
- Camera Picamera2 — Phase 6
- Full `detect_frame` — Phase 5/7

</deferred>

---

*Phase: 03-core-api-contracts*
*Context gathered: 2026-07-03*

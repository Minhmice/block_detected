# Task 1 — Output contract (`detection_contract.py`)

**Status:** Done  
**Completed:** 2026-05-31  
**Owner note:** Implemented and smoke-tested locally (`python -B`).

## Delivered

- Stdlib-only dataclasses/enums (no Pydantic).
- Types: `DetectionResult`, `PointPx`, `CornersPx`, `BoundingBoxPx`, `PickupPose`, `DebugInfo`.
- Enums: `BlockID` (1–4), `BlockLabel`, `DetectionStatus`.
- Helpers: `make_no_detection_result()`, `validate_detection_result()`, `result_to_dict()`, `result_to_json()`.
- Sample payloads: successful block 1, low confidence, no detection (`SAMPLE_OUTPUTS_JSON`).
- **No** OpenCV or image-processing code (by design).

## Validation

- Sample serialization smoke test passed.
- Negative test: `block_id` / `label` mismatch raises `DetectionContractError`.

## Phase 1 remainder

- [x] `detect_block(frame)` public API (stub) — `src/block_detected/pipeline.py`
- [x] Package layout `src/block_detected/` + `pyproject.toml` + root shim

## Maps to requirements

| ID | Status | Notes |
|----|--------|-------|
| CONT-01 | Done | `from block_detected import detect_block` |
| CONT-02 | Done | Synthetic sentinel + samples |
| CONT-03 | Done | `NO_DETECTION` / `MULTIPLE_CANDIDATES` no geometry |

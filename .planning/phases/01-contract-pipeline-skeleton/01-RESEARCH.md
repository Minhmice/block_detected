# Phase 1: Contract & Pipeline Skeleton - Research

**Researched:** 2026-05-31 [VERIFIED: `date +%F`]
**Domain:** Python stdlib contract boundary and public pipeline API skeleton [VERIFIED: `.planning/ROADMAP.md`, `detection_contract.py`]
**Confidence:** HIGH for local contract/API findings; MEDIUM for package-layout recommendation because the repo has no package metadata yet [VERIFIED: `rg --files`; VERIFIED: `find . -maxdepth 3 ...`]

<user_constraints>
## User Constraints

No phase `CONTEXT.md` exists, so there are no additional locked decisions, discretion notes, or deferred ideas beyond project docs and roadmap requirements. [VERIFIED: `gsd-tools init phase-op 1` returned `has_context: false`]

### Locked Decisions

- Use the existing `detection_contract.py` as the integration boundary. [VERIFIED: `.planning/PROJECT.md`; VERIFIED: `.planning/STATE.md`; VERIFIED: `.planning/notes/task-01-contract.md`]
- Phase 1 must expose public `detect_block(frame)` and return validated `DetectionResult` objects; a stub pipeline is acceptable. [VERIFIED: `.planning/ROADMAP.md`; VERIFIED: `.planning/REQUIREMENTS.md`]
- Phase 1 maps to `CONT-01`, `CONT-02`, and `CONT-03`. [VERIFIED: `.planning/ROADMAP.md`; VERIFIED: `.planning/REQUIREMENTS.md`]
- The project explicitly excludes ArUco/AprilTag markers on blocks. [VERIFIED: `.planning/PROJECT.md`; VERIFIED: `.planning/REQUIREMENTS.md`]

### Claude's Discretion

- No phase discretion section exists; package layout, tests, and exact stub behavior should follow the smallest design that satisfies `CONT-01` through `CONT-03`. [VERIFIED: `gsd-tools init phase-op 1`; VERIFIED: repo has only `detection_contract.py` and planning docs from `rg --files`]

### Deferred Ideas (OUT OF SCOPE)

- Camera capture, OpenCV preprocessing, contour geometry, warp, CNN classification, pose calibration, and full reject policy are later phases. [VERIFIED: `.planning/ROADMAP.md`; VERIFIED: `.planning/REQUIREMENTS.md`]
</user_constraints>

<phase_requirements>
## Phase Requirements

| ID | Description | Research Support |
|----|-------------|------------------|
| CONT-01 | Public `detect_block(frame)` returns validated `DetectionResult` matching `detection_contract.py`. [VERIFIED: `.planning/REQUIREMENTS.md`] | Add a `pipeline.detect_block` public function that always passes its return through `validate_detection_result()`. [VERIFIED: `detection_contract.py` exposes `validate_detection_result()` at lines 363-381] |
| CONT-02 | Successful detection populates `block_id`, `confidence`, `center_px`, `corners_px` in TL/TR/BR/BL order, and `angle_deg`. [VERIFIED: `.planning/REQUIREMENTS.md`] | Use the existing sample-success shape as the synthetic success fixture; the contract already validates block identity, finite numeric fields, corner point types, confidence range, and status-specific geometry requirements. [VERIFIED: `detection_contract.py` lines 88-134, 211-321, 418-435] |
| CONT-03 | Rejected or ambiguous frames return appropriate `status` with `debug.rejection_reason` and no fake geometry. [VERIFIED: `.planning/REQUIREMENTS.md`; VERIFIED: `.planning/ROADMAP.md`] | Use `make_no_detection_result()` for ordinary stub rejection and add tests that rejected outputs have nullable geometry. [VERIFIED: `detection_contract.py` lines 324-360] Also resolve the `MULTIPLE_CANDIDATES` contract mismatch before testing ambiguous status with no geometry. [VERIFIED: local smoke probe raised `DetectionContractError` for no-geometry `MULTIPLE_CANDIDATES`] |
</phase_requirements>

## Summary

Phase 1 should be planned as a narrow API and import-structure phase, not as a computer-vision phase. [VERIFIED: `.planning/ROADMAP.md`; VERIFIED: `.planning/notes/task-01-contract.md`] The existing contract is already stdlib-only and validates most field-level and status-level behavior, including enum coercion, finite numeric values, confidence range, block-label matching, nullable geometry for `no_detection` and `invalid_geometry`, JSON conversion, and sample outputs. [VERIFIED: `detection_contract.py` lines 10-15, 61-85, 211-321, 384-473]

The main implementation work is to expose `detect_block(frame)`, keep it fail-safe, and add tests. [VERIFIED: `.planning/STATE.md`; VERIFIED: `.planning/ROADMAP.md`] Unknown real frames should return `no_detection` with a clear debug rejection reason until later detector phases exist, while synthetic test frames can intentionally trigger a valid success result to satisfy `CONT-02`. [VERIFIED: `.planning/ROADMAP.md`; VERIFIED: `detection_contract.py` lines 324-360, 418-435]

**Primary recommendation:** Move the contract into an importable `src/block_detected/` package, leave a root compatibility shim for `detection_contract.py`, add `src/block_detected/pipeline.py::detect_block(frame)`, and validate every public return with `validate_detection_result()`. [VERIFIED: `.planning/notes/task-01-contract.md`; VERIFIED: `.planning/research/ARCHITECTURE.md`; VERIFIED: `detection_contract.py` lines 363-381]

## Project Constraints (from CLAUDE.md)

- The project is a Raspberry Pi / edge vision pipeline for detecting one of four colored cube blocks without ArUco markers. [VERIFIED: `CLAUDE.md`]
- The core value is reliable block ID plus correctly ordered corners and angle for robot pickup, not just a bounding box. [VERIFIED: `CLAUDE.md`; VERIFIED: `.planning/PROJECT.md`]
- The target stack is Python 3, OpenCV, TensorFlow Lite INT8, and Pi-compatible runtime, but Phase 1 should not pull OpenCV or TFLite into the contract boundary. [VERIFIED: `CLAUDE.md`; VERIFIED: `.planning/notes/task-01-contract.md`]
- The output must conform to the existing `DetectionResult` contract in `detection_contract.py`. [VERIFIED: `CLAUDE.md`; VERIFIED: `.planning/PROJECT.md`]
- The existing contract is stdlib-only and intentionally contains no image-processing code. [VERIFIED: `detection_contract.py` lines 1-15; VERIFIED: `.planning/notes/task-01-contract.md`]
- GSD workflow enforcement says file-changing work should happen through GSD entry points unless explicitly bypassed. [VERIFIED: `CLAUDE.md`]
- No project-specific skills were found in `.claude/skills/` or `.agents/skills/`. [VERIFIED: `find .claude/skills .agents/skills -maxdepth 2 -name SKILL.md` returned no files; VERIFIED: `CLAUDE.md`]

## Standard Stack

### Core

| Library | Version | Purpose | Why Standard |
|---------|---------|---------|--------------|
| Python stdlib `dataclasses` | Bundled with local Python 3.14.4; available since Python 3.7. [VERIFIED: `python3 --version`; CITED: https://docs.python.org/3/library/dataclasses.html] | Immutable contract value objects and generated constructors. [VERIFIED: `detection_contract.py` lines 12, 88-249] | The existing contract already uses frozen dataclasses, and Python docs define `@dataclass` as generating methods from annotated fields. [VERIFIED: `detection_contract.py`; CITED: https://docs.python.org/3/library/dataclasses.html] |
| Python stdlib `enum` / `IntEnum` | Bundled with local Python 3.14.4. [VERIFIED: `python3 --version`; CITED: https://docs.python.org/3/library/enum.html] | `BlockID`, `BlockLabel`, and `DetectionStatus`. [VERIFIED: `detection_contract.py` lines 13, 22-48] | `IntEnum` members are integer-compatible, which matches block IDs 1-4 without a custom ID class. [CITED: https://docs.python.org/3/library/enum.html] |
| Python stdlib `json` | Bundled with local Python 3.14.4. [VERIFIED: `python3 --version`; CITED: https://docs.python.org/3/library/json.html] | JSON-compatible integration payloads. [VERIFIED: `detection_contract.py` lines 10, 384-415] | The contract already centralizes JSON conversion and should remain the only serializer for detection results. [VERIFIED: `detection_contract.py` lines 398-415] |
| Python stdlib `unittest` | Bundled with local Python 3.14.4. [VERIFIED: `python3 --version`; VERIFIED: `python3 - <<'PY' import unittest`] | Phase 1 unit tests without adding dependency management. [VERIFIED: pytest missing locally; VERIFIED: no `pyproject.toml` or requirements files found] | `unittest` supports CLI execution and discovery from the standard library, so Phase 1 can get validation coverage without installing pytest. [CITED: https://docs.python.org/3/library/unittest.html] |
| Existing `detection_contract.py` | Repo implementation. [VERIFIED: `detection_contract.py`] | Contract types, validation helpers, sample outputs. [VERIFIED: `.planning/notes/task-01-contract.md`] | It is already the locked integration boundary and implements the behavior Phase 1 must return. [VERIFIED: `.planning/PROJECT.md`; VERIFIED: `.planning/STATE.md`] |

### Supporting

| Library | Version | Purpose | When to Use |
|---------|---------|---------|-------------|
| `pytest` | Not installed locally. [VERIFIED: `importlib.util.find_spec('pytest')` returned missing] | Optional future test runner. [VERIFIED: `CLAUDE.md` stack section recommends pytest for broader project tests] | Do not make Phase 1 depend on it unless adding dependency metadata is explicitly in scope. [VERIFIED: repo has no `pyproject.toml`, setup config, or requirements files] |
| OpenCV / `cv2` | Not installed locally. [VERIFIED: `importlib.util.find_spec('cv2')` returned missing] | Later image processing. [VERIFIED: `.planning/ROADMAP.md` phases 3-4] | Do not import in `detect_block` skeleton; adding it would expand Phase 1 into later-phase work. [VERIFIED: `.planning/ROADMAP.md`; VERIFIED: `.planning/notes/task-01-contract.md`] |
| NumPy | Not installed locally. [VERIFIED: `importlib.util.find_spec('numpy')` returned missing] | Later array/frame processing. [VERIFIED: `CLAUDE.md` stack section] | Avoid requiring NumPy for the stub frame sentinel so tests run in the current environment. [VERIFIED: local dependency probe] |

### Alternatives Considered

| Instead of | Could Use | Tradeoff |
|------------|-----------|----------|
| stdlib dataclasses + explicit validators [VERIFIED: `detection_contract.py`] | Pydantic [ASSUMED] | Adds runtime dependency and contradicts the completed task note that the contract is stdlib-only. [VERIFIED: `.planning/notes/task-01-contract.md`] |
| `unittest` for Phase 1 [CITED: https://docs.python.org/3/library/unittest.html] | `pytest` [VERIFIED: `CLAUDE.md` stack section] | `pytest` is a reasonable later project standard, but it is absent and would require dependency scaffolding before any Phase 1 behavior can be tested. [VERIFIED: local dependency probe; VERIFIED: no package metadata found] |
| Safe no-detection default [VERIFIED: `detection_contract.py` lines 324-360] | Return synthetic success for every non-null frame [ASSUMED] | Fabricating corners for arbitrary real frames violates the success criterion that rejected frames should not get fake geometry. [VERIFIED: `.planning/ROADMAP.md`] |

**Installation:**

```bash
# Phase 1 requires no third-party packages.
python3 --version
python3 -m unittest discover -v
```

**Version verification:** Local environment checks returned Python 3.14.4, missing `pytest`, missing `cv2`, and missing `numpy`. [VERIFIED: `python3 --version`; VERIFIED: importlib probe] No `npm view` checks apply because this phase has no npm packages. [VERIFIED: repo has no JavaScript package files from `rg --files`]

## Architecture Patterns

### Recommended Project Structure

```text
src/
└── block_detected/
    ├── __init__.py              # Re-export public API and contract symbols.
    ├── detection_contract.py    # Existing contract implementation moved here.
    └── pipeline.py              # detect_block(frame) skeleton.
tests/
├── __init__.py                  # Keeps unittest discovery/imports predictable.
├── test_detection_contract.py   # Existing contract behavior regression tests.
└── test_pipeline.py             # CONT-01/02/03 detect_block tests.
detection_contract.py            # Temporary compatibility shim re-exporting package contract.
pyproject.toml                   # Optional only if planner chooses editable package install now.
```

This structure follows the project architecture research that names `src/block_detected/pipeline.py` as the `detect_block()` home, while preserving the current root import during migration. [VERIFIED: `.planning/research/ARCHITECTURE.md`; VERIFIED: current repo has root `detection_contract.py` only]

### Pattern 1: Contract-First Public Boundary

**What:** `detect_block(frame)` should return only `DetectionResult` objects and should call `validate_detection_result()` before returning. [VERIFIED: `.planning/REQUIREMENTS.md`; VERIFIED: `detection_contract.py` lines 363-381]

**When to use:** Every public API return path in Phase 1. [VERIFIED: `CONT-01` in `.planning/REQUIREMENTS.md`]

**Example:**

```python
# Source: repo contract helper at detection_contract.py lines 363-381.
from .detection_contract import DetectionResult, validate_detection_result


def _return(result: DetectionResult) -> DetectionResult:
    return validate_detection_result(result)
```

### Pattern 2: Fail-Safe Stub Policy

**What:** Unknown frames should return `no_detection` with `debug.rejection_reason`, not made-up block identity or corners. [VERIFIED: `.planning/ROADMAP.md`; VERIFIED: `detection_contract.py` lines 313-360]

**When to use:** Until Phase 3+ provides real contour candidates. [VERIFIED: `.planning/ROADMAP.md` phases 3-4]

**Example:**

```python
# Source: repo helper at detection_contract.py lines 324-360.
from .detection_contract import make_no_detection_result, validate_detection_result


def detect_block(frame):
    return validate_detection_result(
        make_no_detection_result(
            method="pipeline_stub",
            rejection_reason="pipeline stub has no detector implementation",
        )
    )
```

### Pattern 3: Explicit Synthetic Success Fixture

**What:** Provide a deterministic synthetic path for tests, separate from ordinary real frames. [VERIFIED: `.planning/ROADMAP.md` allows stub/synthetic detection; VERIFIED: `SAMPLE_SUCCESS_BLOCK_1` exists in `detection_contract.py` lines 418-435]

**When to use:** Unit tests for `CONT-02` before vision stages exist. [VERIFIED: `.planning/REQUIREMENTS.md`]

**Example:**

```python
# Source: repo sample result at detection_contract.py lines 418-435.
from .detection_contract import SAMPLE_SUCCESS_BLOCK_1, validate_detection_result


def _synthetic_success_result():
    return validate_detection_result(SAMPLE_SUCCESS_BLOCK_1)
```

### Anti-Patterns to Avoid

- **Importing `cv2` in Phase 1:** OpenCV is absent locally and belongs to later preprocessing/geometry phases. [VERIFIED: local import probe; VERIFIED: `.planning/ROADMAP.md` phases 3-4]
- **Duplicating `DetectionResult` or JSON serializers:** The existing contract already owns result types, validation, and JSON conversion. [VERIFIED: `detection_contract.py` lines 211-415]
- **Returning success for arbitrary real frames:** This fabricates geometry before any detector exists and conflicts with the reject/no-fake-geometry success criterion. [VERIFIED: `.planning/ROADMAP.md`; VERIFIED: `detection_contract.py` lines 313-360]
- **Testing `multiple_candidates` as no-geometry without a contract fix:** The current contract rejects no-geometry `MULTIPLE_CANDIDATES`. [VERIFIED: local smoke probe; VERIFIED: `detection_contract.py` lines 304-312]

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| Contract validation | A second validator inside `pipeline.py`. [VERIFIED: current validator exists] | `validate_detection_result()`. [VERIFIED: `detection_contract.py` lines 363-381] | It centralizes enum, numeric, identity, and status rules already required by `CONT-01`. [VERIFIED: `detection_contract.py` lines 262-321] |
| No-detection result construction | Repeated nullable-field constructors. [VERIFIED: current helper exists] | `make_no_detection_result()`. [VERIFIED: `detection_contract.py` lines 324-360] | It ensures candidate fields are null and debug rejection reason is populated consistently. [VERIFIED: `detection_contract.py` lines 343-359] |
| JSON payload conversion | Ad hoc `__dict__` or enum conversion. [ASSUMED] | `result_to_dict()` / `result_to_json()`. [VERIFIED: `detection_contract.py` lines 384-415] | The helper handles dataclasses, enums, mappings, lists, and tuples in one place. [VERIFIED: `detection_contract.py` lines 384-395] |
| Phase 1 image processing | Stub contour, warp, or classifier logic. [ASSUMED] | A safe stub plus synthetic test fixture. [VERIFIED: `.planning/ROADMAP.md`; VERIFIED: `.planning/notes/task-01-contract.md`] | Camera, preprocessing, geometry, and classifier are explicitly later phases. [VERIFIED: `.planning/ROADMAP.md`] |
| Test execution | Custom test harness script. [ASSUMED] | `python3 -m unittest discover -v`. [CITED: https://docs.python.org/3/library/unittest.html] | `unittest` discovery is built into Python and works without third-party installs. [CITED: https://docs.python.org/3/library/unittest.html] |

**Key insight:** The hard part of Phase 1 is preserving safety semantics at the boundary, not recognizing blocks. [VERIFIED: `.planning/ROADMAP.md`; VERIFIED: `.planning/REQUIREMENTS.md`] Plan the stub so later phases can replace internals without changing the public contract. [VERIFIED: `.planning/research/ARCHITECTURE.md`]

## Common Pitfalls

### Pitfall 1: `MULTIPLE_CANDIDATES` Semantics Conflict

**What goes wrong:** A test that expects ambiguous frames to return `multiple_candidates` without geometry will fail today. [VERIFIED: local smoke probe; VERIFIED: `detection_contract.py` lines 304-312]

**Why it happens:** Current validation groups `MULTIPLE_CANDIDATES` with `OK` and `LOW_CONFIDENCE`, so it requires block identity and geometry. [VERIFIED: `detection_contract.py` lines 304-312]

**How to avoid:** Either revise the contract so `MULTIPLE_CANDIDATES` is a no-candidate rejection status, or keep Phase 1 ambiguous tests on `NO_DETECTION`/`INVALID_GEOMETRY` and defer `MULTIPLE_CANDIDATES` semantics to Phase 7. [VERIFIED: `.planning/ROADMAP.md` phases 1 and 7]

**Warning signs:** A no-geometry `DetectionResult(... status=DetectionStatus.MULTIPLE_CANDIDATES)` raises `DetectionContractError`. [VERIFIED: local smoke probe]

### Pitfall 2: Import Path Churn

**What goes wrong:** Moving `detection_contract.py` into a package can break current root-level imports. [VERIFIED: current repo has root `detection_contract.py`; VERIFIED: no package directory exists]

**Why it happens:** The repo currently has no `src/`, no `block_detected/` package, and no package metadata. [VERIFIED: `rg --files`; VERIFIED: `find . -maxdepth 3 ...`]

**How to avoid:** Leave a root `detection_contract.py` shim that re-exports from `src.block_detected` or postpone the move and create a flat API module for this phase. [VERIFIED: current root module exists; ASSUMED: external callers may already import root `detection_contract`]

**Warning signs:** Tests pass only when run from one working directory, or imports require manual `PYTHONPATH` edits. [ASSUMED]

### Pitfall 3: Stub Fabricates Real Detection Geometry

**What goes wrong:** `detect_block(frame)` returns sample corners for real frames before a detector exists. [ASSUMED]

**Why it happens:** The success criterion requires a successful stub/synthetic path, which can be misread as success for every input. [VERIFIED: `.planning/ROADMAP.md`]

**How to avoid:** Use an explicit synthetic sentinel or helper for success tests and return `no_detection` for ordinary frames. [VERIFIED: `.planning/ROADMAP.md`; VERIFIED: `make_no_detection_result()` in `detection_contract.py`]

**Warning signs:** An empty object or arbitrary byte buffer produces `status=ok`. [ASSUMED]

### Pitfall 4: Tests Added After API Choices

**What goes wrong:** The public import path and rejection semantics become accidental. [ASSUMED]

**Why it happens:** The repo currently has no tests, and `python3 -m unittest discover -v` ran zero tests with exit code 5. [VERIFIED: local unittest discovery run]

**How to avoid:** Add Wave 0 tests for `CONT-01`, `CONT-02`, and `CONT-03` before or alongside the pipeline module. [VERIFIED: `.planning/REQUIREMENTS.md`; VERIFIED: `.planning/config.json` has `nyquist_validation: true`]

**Warning signs:** Manual smoke snippets are the only validation artifact. [VERIFIED: `.planning/notes/task-01-contract.md` says Task 1 was smoke-tested locally]

## Code Examples

Verified patterns from local contract and official stdlib docs:

### Public API Return Validation

```python
# Source: detection_contract.py lines 363-381.
from .detection_contract import DetectionResult, validate_detection_result


def _validated(result: DetectionResult) -> DetectionResult:
    return validate_detection_result(result)
```

### Safe Stub Rejection

```python
# Source: detection_contract.py lines 324-360.
from .detection_contract import make_no_detection_result, validate_detection_result


def detect_block(frame):
    return validate_detection_result(
        make_no_detection_result(
            method="pipeline_stub",
            rejection_reason="no detector implemented in Phase 1 stub",
        )
    )
```

### `unittest` Contract Test Shape

```python
# Source: Python unittest CLI/discovery docs at https://docs.python.org/3/library/unittest.html.
import unittest

from block_detected import detect_block
from block_detected.detection_contract import DetectionResult, validate_detection_result


class DetectBlockContractTests(unittest.TestCase):
    def test_detect_block_returns_valid_result(self):
        result = detect_block(object())
        self.assertIsInstance(result, DetectionResult)
        self.assertIs(validate_detection_result(result), result)
```

### Compatibility Shim Shape

```python
# Source: current root module is detection_contract.py; package move is recommended by architecture notes.
from block_detected.detection_contract import *  # noqa: F401,F403
```

## State of the Art

| Old Approach | Current Approach | When Changed | Impact |
|--------------|------------------|--------------|--------|
| Direct root-only module imports. [VERIFIED: current repo has root `detection_contract.py`] | Importable package API with `detect_block` re-exported from `block_detected`. [VERIFIED: `.planning/research/ARCHITECTURE.md`] | Phase 1 planning point. [VERIFIED: `.planning/STATE.md`] | Integrators get a stable public entry point before camera and ML stages exist. [VERIFIED: `.planning/ROADMAP.md`] |
| Manual smoke snippets only. [VERIFIED: `.planning/notes/task-01-contract.md`] | Repeatable `unittest` tests mapped to requirements. [CITED: https://docs.python.org/3/library/unittest.html; VERIFIED: `.planning/config.json`] | Phase 1 planning point. [VERIFIED: no tests found] | Validation can gate future refactors of the contract and pipeline skeleton. [VERIFIED: `nyquist_validation: true` in `.planning/config.json`] |
| Fabricated sample output for all frames. [ASSUMED] | Safe rejection by default plus explicit synthetic success fixture. [VERIFIED: `.planning/ROADMAP.md`; VERIFIED: `detection_contract.py` sample outputs] | Phase 1 planning point. [VERIFIED: `.planning/ROADMAP.md`] | Rejected frames avoid fake corner geometry while tests still exercise successful result fields. [VERIFIED: `.planning/ROADMAP.md`; VERIFIED: `detection_contract.py`] |

**Deprecated/outdated:**

- No deprecated Phase 1 API was found because `detect_block(frame)` does not exist yet. [VERIFIED: `rg --files`; VERIFIED: `rg "def detect_block|detect_block\\("` found no source occurrence outside planning docs]
- Adding OpenCV/TFLite to Phase 1 is premature rather than deprecated. [VERIFIED: `.planning/ROADMAP.md`; VERIFIED: local `cv2` missing]

## Assumptions Log

| # | Claim | Section | Risk if Wrong |
|---|-------|---------|---------------|
| A1 | Pydantic is an alternative but should not be used for this phase. | Standard Stack / Don't Hand-Roll | If the user later requires Pydantic schemas for integration, the planner would need a dependency and serializer plan. |
| A2 | External callers may already import root `detection_contract`. | Common Pitfalls | If no external callers exist, the compatibility shim is still low-cost but not strictly necessary. |
| A3 | Returning sample geometry for arbitrary real frames would be unsafe. | Common Pitfalls / State of the Art | If the integrator explicitly wants all non-null frames to return a sample success during simulation, the stub policy should be changed and clearly labeled. |
| A4 | Custom test harness scripts are unnecessary for Phase 1. | Don't Hand-Roll | If the project later standardizes on custom hardware smoke scripts, unittest should remain the fast unit layer and the script can be an integration layer. |
| A5 | Ad hoc `__dict__` or enum conversion is the likely hand-rolled JSON alternative. | Don't Hand-Roll | Planner might miss a different serializer risk, but the mitigation remains to use `result_to_dict()` / `result_to_json()`. |
| A6 | Stub contour, warp, or classifier logic is the likely hand-rolled image-processing temptation in Phase 1. | Don't Hand-Roll | Planner might over-scope Phase 1 if it tries to implement vision behavior early. |
| A7 | Import-path problems may appear as working-directory-specific test failures or manual `PYTHONPATH` needs. | Common Pitfalls | Planner should include import tests if it creates `src/` layout. |
| A8 | Public import path and rejection semantics become accidental if tests are added after API choices. | Common Pitfalls | Planner should create tests before or alongside the API skeleton. |
| A9 | No downstream consumer depends on geometry-bearing `MULTIPLE_CANDIDATES` yet. | Open Questions | If a consumer already expects geometry for `MULTIPLE_CANDIDATES`, changing validation now would be a breaking change. |
| A10 | A flat `block_detected/` package is simpler than `src/` when package metadata is not added. | Open Questions | Planner may choose `src/` plus `pyproject.toml` instead; either route needs import tests. |
| A11 | Manual uncommitted file or direct git commands are acceptable fallbacks if GSD commit tooling fails. | Environment Availability | If the workflow requires GSD-only commits, planner should repair GSD tooling instead of bypassing it. |
| A12 | Plain Python objects or mappings are sufficient for synthetic Phase 1 tests without NumPy. | Environment Availability | If integrators require ndarray-like frames immediately, Phase 1 would need NumPy or a typed frame protocol. |
| A13 | Malformed or unexpected frame objects are a realistic denial-of-service risk for the stub API. | Security Domain | Planner should still keep error handling minimal and fail closed. |
| A14 | The research validity window of 2026-06-30 is appropriate for Phase 1 stdlib/API findings. | Metadata | Planner should re-check environment and docs earlier if package or Python-version decisions change. |

## Open Questions (RESOLVED)

1. **Should Phase 1 correct `MULTIPLE_CANDIDATES` validation now?** — **RESOLVED: Yes (Plan 01-03).** Move `MULTIPLE_CANDIDATES` to the no-candidate rejection group (nullable geometry, `pickup_pose=None`). Aligns with ROADMAP reject semantics; no downstream consumer requires geometry-bearing `multiple_candidates` yet.

2. **Should package metadata be added in Phase 1?** — **RESOLVED: Yes (Plan 01-02).** Add minimal `pyproject.toml` with `src/` layout and editable install so `from block_detected import detect_block` works from repo root without manual `PYTHONPATH`. Root `detection_contract.py` shim re-exports via `from block_detected.detection_contract import *`.

## Environment Availability

| Dependency | Required By | Available | Version | Fallback |
|------------|-------------|-----------|---------|----------|
| Python 3 | Contract and pipeline skeleton. [VERIFIED: project constraints] | Yes. [VERIFIED: `python3 --version`] | 3.14.4 local. [VERIFIED: `python3 --version`] | Avoid APIs newer than Pi target Python unless explicitly needed. [VERIFIED: `CLAUDE.md` stack notes Pi Python 3.11.x] |
| `unittest` | Phase 1 unit tests. [CITED: https://docs.python.org/3/library/unittest.html] | Yes. [VERIFIED: `import unittest`] | stdlib. [VERIFIED: local import] | None needed. |
| `git` | Optional research commit. [VERIFIED: `.planning/config.json` has `commit_docs: true`] | Yes. [VERIFIED: `git --version`] | 2.53.0. [VERIFIED: `git --version`] | Manual uncommitted file if commit fails. [ASSUMED] |
| Node / GSD tools | Phase metadata and optional commit. [VERIFIED: `gsd-tools init phase-op 1`] | Yes. [VERIFIED: `node --version`] | v24.14.0. [VERIFIED: `node --version`] | Direct git commands if GSD helper fails. [ASSUMED] |
| pytest | Optional broader test runner. [VERIFIED: `CLAUDE.md` stack notes] | No. [VERIFIED: importlib probe] | None. [VERIFIED: importlib probe] | Use stdlib `unittest` for Phase 1. [CITED: https://docs.python.org/3/library/unittest.html] |
| OpenCV / `cv2` | Later vision phases only. [VERIFIED: `.planning/ROADMAP.md`] | No. [VERIFIED: importlib probe] | None. [VERIFIED: importlib probe] | Do not require it in Phase 1. [VERIFIED: `.planning/notes/task-01-contract.md`] |
| NumPy | Later frame/geometry phases only. [VERIFIED: `CLAUDE.md` stack notes] | No. [VERIFIED: importlib probe] | None. [VERIFIED: importlib probe] | Use plain Python objects or mappings for synthetic Phase 1 tests. [ASSUMED] |

**Missing dependencies with no fallback:**

- None for Phase 1. [VERIFIED: Python stdlib is sufficient for contract, pipeline stub, and unittest validation]

**Missing dependencies with fallback:**

- `pytest` is missing; use `unittest` for Phase 1. [VERIFIED: local dependency probe; CITED: https://docs.python.org/3/library/unittest.html]
- `cv2` and `numpy` are missing; keep image-processing behavior out of Phase 1. [VERIFIED: local dependency probe; VERIFIED: `.planning/ROADMAP.md`]

## Validation Architecture

### Test Framework

| Property | Value |
|----------|-------|
| Framework | Python stdlib `unittest`. [CITED: https://docs.python.org/3/library/unittest.html; VERIFIED: local import] |
| Config file | None. [VERIFIED: no `pytest.ini`, `tox.ini`, `noxfile.py`, `pyproject.toml`, or setup config found] |
| Quick run command | `python3 -m unittest tests/test_pipeline.py -v` [CITED: https://docs.python.org/3/library/unittest.html] |
| Full suite command | `python3 -m unittest discover -v` [CITED: https://docs.python.org/3/library/unittest.html] |

### Phase Requirements to Test Map

| Req ID | Behavior | Test Type | Automated Command | File Exists? |
|--------|----------|-----------|-------------------|--------------|
| CONT-01 | `detect_block(frame)` returns a `DetectionResult` and `validate_detection_result(result)` returns the same object. [VERIFIED: `.planning/REQUIREMENTS.md`; VERIFIED: `detection_contract.py` lines 363-381] | unit | `python3 -m unittest tests/test_pipeline.py -v` | No, Wave 0. [VERIFIED: no tests found] |
| CONT-02 | Synthetic success result populates `block_id`, `confidence`, `center_px`, `corners_px` TL/TR/BR/BL, and `angle_deg`. [VERIFIED: `.planning/REQUIREMENTS.md`; VERIFIED: `SAMPLE_SUCCESS_BLOCK_1` lines 418-435] | unit | `python3 -m unittest tests/test_pipeline.py -v` | No, Wave 0. [VERIFIED: no tests found] |
| CONT-03 | Rejected frames return `status` with `debug.rejection_reason` and no candidate geometry. [VERIFIED: `.planning/REQUIREMENTS.md`; VERIFIED: `make_no_detection_result()` lines 324-360] | unit | `python3 -m unittest tests/test_pipeline.py -v` | No, Wave 0. [VERIFIED: no tests found] |

### Sampling Rate

- **Per task commit:** `python3 -m unittest tests/test_pipeline.py -v` once the file exists. [CITED: https://docs.python.org/3/library/unittest.html]
- **Per wave merge:** `python3 -m unittest discover -v`. [CITED: https://docs.python.org/3/library/unittest.html]
- **Phase gate:** Full suite green before `/gsd-verify-work`. [VERIFIED: `.planning/config.json` has `nyquist_validation: true`]

### Wave 0 Gaps

- [ ] `tests/__init__.py` - keeps tests importable under discovery. [CITED: https://docs.python.org/3/library/unittest.html]
- [ ] `tests/test_pipeline.py` - covers `CONT-01`, `CONT-02`, and `CONT-03`. [VERIFIED: `.planning/REQUIREMENTS.md`]
- [ ] Optional `tests/test_detection_contract.py` - locks current sample serialization and mismatch guard before moving the contract into a package. [VERIFIED: `.planning/notes/task-01-contract.md`; VERIFIED: `detection_contract.py` samples]
- [ ] Decide whether to adjust `MULTIPLE_CANDIDATES` semantics before writing ambiguous-frame assertions. [VERIFIED: local smoke probe]

## Security Domain

Security enforcement is enabled by default because `.planning/config.json` does not explicitly set `security_enforcement: false`. [VERIFIED: `.planning/config.json`]

### Applicable ASVS Categories

| ASVS Category | Applies | Standard Control |
|---------------|---------|------------------|
| V2 Authentication | No. [VERIFIED: Phase 1 has no users, credentials, or auth flow in roadmap] | None for Phase 1. [VERIFIED: `.planning/ROADMAP.md`] |
| V3 Session Management | No. [VERIFIED: Phase 1 has no sessions in roadmap] | None for Phase 1. [VERIFIED: `.planning/ROADMAP.md`] |
| V4 Access Control | No. [VERIFIED: Phase 1 is local library API only] | None for Phase 1. [VERIFIED: `.planning/ROADMAP.md`] |
| V5 Input Validation | Yes. [VERIFIED: `detect_block(frame)` accepts external frame object; contract validates outputs] | Fail closed to `no_detection`; validate every output with `validate_detection_result()`. [VERIFIED: `detection_contract.py` lines 262-381] |
| V6 Cryptography | No. [VERIFIED: Phase 1 has no secrets, tokens, or cryptographic operations] | Do not add cryptography. [VERIFIED: `.planning/ROADMAP.md`] |

### Known Threat Patterns for Phase 1 Stack

| Pattern | STRIDE | Standard Mitigation |
|---------|--------|---------------------|
| Malformed or unexpected frame object causes exception instead of safe result. [ASSUMED] | Denial of Service | Keep the stub input handling minimal and return validated `no_detection` for unsupported frames. [VERIFIED: `make_no_detection_result()` exists; VERIFIED: `.planning/ROADMAP.md`] |
| Non-finite numeric values leak into JSON payloads. [VERIFIED: Python json can serialize NaN/Infinity by default; VERIFIED: contract rejects non-finite numbers] | Tampering | Use `_require_number()` through `DetectionResult` construction and `validate_detection_result()`. [CITED: https://docs.python.org/3/library/json.html; VERIFIED: `detection_contract.py` lines 79-85, 262-292] |
| Ambiguous-frame status carries fabricated geometry. [VERIFIED: Phase success criterion forbids fake geometry] | Spoofing / Tampering | Keep rejected statuses geometry-null, and fix or defer `MULTIPLE_CANDIDATES` semantics explicitly. [VERIFIED: `.planning/ROADMAP.md`; VERIFIED: local smoke probe] |

## Sources

### Primary (HIGH confidence)

- `detection_contract.py` - contract types, validators, JSON conversion, sample outputs, and status behavior. [VERIFIED: repo]
- `.planning/ROADMAP.md` - Phase 1 goal, success criteria, dependencies, and later-phase boundaries. [VERIFIED: repo]
- `.planning/REQUIREMENTS.md` - `CONT-01`, `CONT-02`, `CONT-03`, and out-of-scope constraints. [VERIFIED: repo]
- `.planning/PROJECT.md` - project constraints and validated contract note. [VERIFIED: repo]
- `.planning/STATE.md` - current Phase 1 status and pending `detect_block` task. [VERIFIED: repo]
- `.planning/notes/task-01-contract.md` - completed contract task and remaining package/API work. [VERIFIED: repo]
- `CLAUDE.md` - project constraints, stack notes, and GSD workflow directives. [VERIFIED: repo]
- Python dataclasses docs - dataclass behavior and stdlib source. [CITED: https://docs.python.org/3/library/dataclasses.html]
- Python enum docs - `IntEnum` integer-compatible behavior. [CITED: https://docs.python.org/3/library/enum.html]
- Python json docs - `json.dumps`, ordering, and non-finite JSON behavior. [CITED: https://docs.python.org/3/library/json.html]
- Python unittest docs - CLI and discovery commands. [CITED: https://docs.python.org/3/library/unittest.html]

### Secondary (MEDIUM confidence)

- `.planning/research/ARCHITECTURE.md` - project architecture recommendation for `src/block_detected/pipeline.py`. [VERIFIED: repo, generated research]
- `.planning/research/PITFALLS.md` - broader pipeline pitfalls and contract mismatch risk. [VERIFIED: repo, generated research]
- `.planning/research/SUMMARY.md` and `.planning/research/FEATURES.md` - project roadmap shape and v1/v2 split. [VERIFIED: repo, generated research]

### Tertiary (LOW confidence)

- Assumptions listed in the Assumptions Log. [VERIFIED: this document]

## Metadata

**Confidence breakdown:**

- Standard stack: HIGH - Phase 1 depends on existing repo code and Python stdlib, both verified locally and against official Python docs. [VERIFIED: local probes; CITED: docs.python.org]
- Architecture: MEDIUM - `src/block_detected/` matches prior project research and task notes, but the repo has no package metadata yet. [VERIFIED: `.planning/research/ARCHITECTURE.md`; VERIFIED: `rg --files`]
- Pitfalls: HIGH for `MULTIPLE_CANDIDATES` mismatch and missing tests because both were reproduced locally; MEDIUM for external import compatibility because no external callers are visible in repo. [VERIFIED: local smoke probe; VERIFIED: no tests found; ASSUMED]
- Validation: HIGH - `unittest` is available locally, official docs support discovery, and no existing tests are present. [VERIFIED: local import and discovery run; CITED: https://docs.python.org/3/library/unittest.html]

**Research date:** 2026-05-31 [VERIFIED: `date +%F`]
**Valid until:** 2026-06-30 for Phase 1 stdlib/API findings; re-check environment before later OpenCV/TFLite phases. [ASSUMED]

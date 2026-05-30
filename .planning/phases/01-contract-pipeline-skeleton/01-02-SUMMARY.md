---
phase: 01-contract-pipeline-skeleton
plan: 02
subsystem: api
tags: [detect_block, package, pyproject]
requires:
  - plan: 01
    provides: unittest API expectations
provides:
  - src/block_detected package
  - detect_block(frame) skeleton
  - root detection_contract shim
tech-stack:
  added: [setuptools via pyproject.toml]
  patterns: ["validate_detection_result on every return path"]
key-files:
  created: [pyproject.toml, src/block_detected/__init__.py, src/block_detected/detection_contract.py, src/block_detected/pipeline.py]
  modified: [detection_contract.py]
key-decisions:
  - "src/ layout with editable install in .venv"
requirements-completed: [CONT-01, CONT-02, CONT-03]
duration: 10min
completed: 2026-05-31
---

# Phase 01 Plan 02 Summary

**Importable `block_detected` package exposes validated `detect_block` with safe no-detection default.**

## Accomplishments

- Moved contract into `src/block_detected/detection_contract.py`; root file is compatibility shim.
- Implemented `pipeline.detect_block` with synthetic sentinels and ordinary-frame rejection.
- Added `pyproject.toml` for editable installs (use project `.venv` on PEP 668 hosts).

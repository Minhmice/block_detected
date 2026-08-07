---
status: resolved
trigger: ModuleNotFoundError: No module named 'block_detected.tui' when selecting TUI (option 2) from python main.py
created: 2026-08-07
updated: 2026-08-07
---

## Symptoms

- **Expected:** TUI dashboard launches after selecting option 2
- **Actual:** `ModuleNotFoundError: No module named 'block_detected.tui'`
- **Reproduction:** `python main.py` → choose 2 (TUI)

## Current Focus

hypothesis: Source moved to block_detected_v1 but block_detected package on disk is empty namespace (pycache only)
next_action: restore block_detected package from v1 and fix tui __init__ import

## Evidence

- `src/block_detected` had 0 `.py` files, only `__pycache__` subdirs + `block_detected.json`
- TUI source lives in `src/block_detected_v1/tui/`
- `import block_detected` returned `__file__: None` (namespace package shadowing)
- `block_detected_v1/tui/__init__.py` used broken `from tui.app import main`

## Resolution

root_cause: Repo cleanup (c850d5c) moved library to `block_detected_v1/` but left ghost `src/block_detected/` dirs with only bytecode. Python resolved empty namespace package `block_detected` without `tui` submodule.
fix: Rsync `block_detected_v1` → `block_detected`; fix `tui/__init__.py` import to `block_detected.tui.app`
verification: `python -c "from block_detected.tui.app import main"` succeeds
files_changed: src/block_detected/** (restored), src/block_detected/tui/__init__.py, src/block_detected_v1/tui/__init__.py

# Phase 5: GUI and runtime hardening for production UAT - Context

**Gathered:** 2026-06-07
**Status:** Ready for planning
**Mode:** Auto-generated (autonomous)

<domain>
## Phase Boundary

Harden GUI/runtime for production UAT: worker shutdown safety, stop-pending state, run generation guards, config restart vs hot-reload UX, error surfacing, metrics display stability.

</domain>

<decisions>
## Implementation Decisions

### Hardening Focus
- Do not set frame_thread=None until QThread finished
- Stale frame_ready/error signals ignored via run generation
- Restart-required config changes show clear status

### Claude's Discretion
Retroactive closure — verify UAT criteria from 05-UAT.md if exists, add missing tests/docs.

</decisions>

<code_context>
## Existing Code Insights

- `apps/gui/app.py` — worker thread lifecycle
- `.planning/phases/05-gui-and-runtime-hardening-for-production-uat/05-UAT.md` — UAT checklist
- `runtime/config_apply.py` — hot vs restart keys

</code_context>

<specifics>
Close phase against 05-UAT.md manual criteria where automatable.

</specifics>

<deferred>
None

</deferred>

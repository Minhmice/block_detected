# External Integrations

**Analysis Date:** 2026-06-02

## APIs & External Services

**None in application code** — fully offline/local.

**Transitive (via Ultralytics):**
- Optional download/checks from Ultralytics hub on first run — not called directly from project modules

## Data Storage

**Model weights:**
- Local directory `models/*.pt` (gitignored except `.gitkeep`)
- Discovery: `detection/yolo/loader.py` → `discover_model_paths()`

**Configuration:**
- Optional `block_detected.toml` at project root
- Load/save: `runtime/config_store.py`

**No database, no object storage, no cache service.**

## Authentication & Identity

Not applicable.

## Monitoring & Observability

**Logging:**
- Python `logging` via `runtime/logging_setup.py`
- Ring buffer handler `LogBufferHandler` for future GUI log panel

**Metrics:**
- In-process only: `runtime/metrics.py` (FPS, stage latencies)
- Exposed on status bar when `ui.show_fps_in_status` is true

## CI/CD & Deployment

Not configured in repo.

## Environment Configuration

**Required:**
- `models/*.pt` present for inference

**Optional:**
- `block_detected.toml` — overrides `AppConfig` defaults

**Secrets:** None

## Webhooks & Callbacks

None.

---

*Integration audit: 2026-06-02*

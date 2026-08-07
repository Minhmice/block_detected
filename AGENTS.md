# Agent guide — Block Detected v1

## Layout

```
src/
├── block_detected/           # library + config + TUI
│   ├── block_detected.json   # detection config (edit here)
│   ├── config/, core/, detection/, io/, runtime/, vision/
│   └── tui/                  # Textual dashboard app
├── view/                     # OpenCV detection app
└── stream/                   # Pi JPEG server + LAN viewer
```

Repo root: `main.py` (launcher), `bootstrap.py` (device + auto-install), `models/`, `pyproject.toml`

**Dependency rules:**
- `view` → `block_detected.runtime`
- `block_detected.tui` → `block_detected.runtime`
- `stream` → standalone (no `block_detected` import)

## Change map

| Goal | Edit here |
|------|-----------|
| JSON config | `block_detected/block_detected.json`, `config/store.py` |
| OpenCV view | `src/view/` |
| TUI | `src/block_detected/tui/` |
| Pi stream | `src/stream/` |
| Detection pipeline | `block_detected/runtime/` |
| Launcher / picker | `main.py` |
| Bootstrap (device, pip) | `bootstrap.py` |
| Platform detect | `block_detected/runtime/platform.py` |

## Run

```bash
python main.py                    # bootstrap + device-aware picker
python main.py --no-install       # skip auto pip
python main.py --install-pi       # Pi 5 deps only (no CUDA extras)
python main.py --view
python main.py --tui
python main.py --stream
python main.py --stream viewer
```

## Do not edit

- `models/*.pt`

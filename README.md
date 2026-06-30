# Block Detected v1

Nhận diện khối/vật thể realtime bằng **YOLO (Ultralytics)** trên webcam. Ba app qua `main.py`:

| App | Lệnh |
|-----|------|
| **View** | `python main.py --view` — OpenCV preview + detection (desktop) |
| **TUI** | `python main.py --tui` — Textual dashboard |
| **Stream** | `python main.py --stream` — Pi JPEG server; `python main.py --stream viewer` — LAN viewer |

Config detection: [`src/block_detected/block_detected.json`](src/block_detected/block_detected.json) — sửa trực tiếp; trong view phím **`r`** reload.

> Contributor: xem [AGENTS.md](AGENTS.md).

## Cài đặt

`python main.py` **tự detect thiết bị** và **cài package nếu thiếu** (không hỏi xác nhận):

| Thiết bị | Auto-install |
|----------|----------------|
| **Desktop** (Mac / Windows / Linux) | `pip install -e ".[view]"` |
| **Raspberry Pi** | `pip install -r requirements-pi.txt` → `pip install -e . --no-deps` |

Tắt auto-install: `--no-install`. Force reinstall: `--install`.

Cài thủ công:

```bash
pip install -e .                  # YOLO + TUI
pip install -e ".[view]"            # OpenCV window (view app)
pip install -e ".[viewer]"          # stream LAN viewer (tkinter)
pip install -e ".[dev]"             # pytest
```

**Raspberry Pi** (hoặc để bootstrap tự cài):

```bash
pip install -r requirements-pi.txt
pip install -e . --no-deps
python main.py --stream
python main.py --tui
```

## Chạy

```bash
python main.py                    # device-aware picker
```

**Desktop menu:** 1 View (mặc định) · 2 TUI · 3 Stream LAN viewer  
**Pi menu:** 1 Stream · 2 TUI (mặc định) — không offer View (headless)

Không có TTY: desktop → View, Pi → TUI.

## Cấu trúc

```
src/block_detected/   # library + block_detected.json + tui/
src/view/             # OpenCV app
src/stream/           # Pi stream server + viewer
models/               # YOLO weights (.pt)
```

## Tests

```bash
python -m pytest tests/ -q
```

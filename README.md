# Block Detected v1

Nhận diện khối/vật thể realtime bằng **YOLO (Ultralytics)** trên webcam. Ba app qua `main.py`:

| App | Lệnh |
|-----|------|
| **View** | `python main.py --view` — OpenCV preview + detection (desktop) |
| **TUI** | `python main.py --tui` — Textual dashboard |
| **Stream** | `python main.py --stream` — Pi JPEG server; `python main.py --stream viewer` — LAN viewer |
| **Target** | `python main.py target --model pose11-fp16.onnx` — headless JSONL targeting |

Config detection: [`src/block_detected/block_detected.json`](src/block_detected/block_detected.json) — sửa trực tiếp; trong view phím **`r`** reload.

> Contributor: xem [AGENTS.md](AGENTS.md).

## Cài đặt

`python main.py` **tự detect thiết bị** và **cài package nếu thiếu** (không hỏi xác nhận):

| Thiết bị | Auto-install |
|----------|----------------|
| **Desktop** (Mac / Windows / Linux) | `pip install -e ".[view]"` |
| **Raspberry Pi** | `python main.py --install-pi` (hoặc `bash install-pi.sh`) |

Tắt auto-install: `--no-install`. Force reinstall: `--install`.

Cài thủ công:

```bash
pip install -e .                  # YOLO + TUI
pip install -e ".[view]"            # OpenCV window (view app)
pip install -e ".[viewer]"          # stream LAN viewer (tkinter)
pip install -e ".[dev]"             # pytest
```

**Raspberry Pi 5** (không kéo CUDA như `pip install -e .` hay `.[all]`):

```bash
python main.py --install-pi          # khuyến nghị
# hoặc
bash install-pi.sh
# hoặc thủ công
pip install -r requirements-pi.txt && pip install -e . --no-deps

python main.py --no-install --stream
python main.py --no-install --tui
```

## Chạy

```bash
python main.py                    # device-aware picker
```

**Desktop menu:** 1 View (mặc định) · 2 TUI · 3 Stream LAN viewer  
**Pi menu:** 1 Stream · 2 TUI (mặc định) — không offer View (headless)

Không có TTY: desktop → View, Pi → TUI.

### Pi targeting headless

```bash
# Chạy model được chọn; mỗi frame in một JSON object
python main.py --no-install target --model pose11-fp16.onnx

# Chạy hữu hạn 300 frame, lọc theo class name hoặc class ID
python main.py --no-install target --model pose11-fp16.onnx --frames 300 --class person

# Kiểm tra mọi model trong models/ trên cùng một camera frame
python main.py --no-install target --check-all
```

Target dùng tâm bounding box cho detect, pose, segment và OBB. `error_norm` nằm trong khoảng gần `[-1, 1]`; X dương sang phải, Y dương xuống dưới. Classification được báo `unsupported`. Model lỗi được báo riêng và không làm `--check-all` dừng sớm.

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

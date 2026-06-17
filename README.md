# Block Detected

Nhận diện khối/vật thể realtime bằng **YOLO (Ultralytics)** trên webcam. Cùng một runtime engine (`WebcamEngine`) có thể chạy qua **GUI desktop** (PySide6) hoặc **TUI terminal** (Textual/Rich).

> Contributor / AI agent: xem [AGENTS.md](AGENTS.md) để biết sửa module nào.

## Tính năng

| Thành phần | Mô tả |
|------------|--------|
| **GUI** | **ROBO-VISION OS** desktop (PySide6) — layout từ `example_ui/stitch_block_pickup_vision_console/` |
| **TUI** | Dashboard terminal: FPS, latency, bảng detection, event log — không cửa sổ preview |
| **Pi stream** | `stream_server.py` / `view_client.py` — JPEG qua TCP (Raspberry Pi ↔ máy xem) |

GUI native thay cho hướng FastAPI + browser (đã gỡ khỏi project).

Post-processing: lọc confidence, diện tích, edge box, merge trùng IoU, ổn định theo thời gian (`stability.*` trong config).

## Yêu cầu

- **Python** 3.10+ (khuyến nghị 3.11+)
- **Webcam** (cho GUI/TUI detection local)
- **GPU NVIDIA** — tùy chọn
- **macOS + Homebrew Python:** nếu dùng `view_client.py` với cửa sổ tkinter: `brew install python-tk@3.14`

## Cài đặt

| Profile | Lệnh | Gồm |
|---------|------|-----|
| **Đầy đủ** (desktop) | `pip install -e .` | YOLO + GUI (PySide6) + TUI (textual/rich) |
| **Raspberry Pi** (nhẹ) | `pip install -r requirements-pi.txt && pip install -e . --no-deps` | YOLO + TUI, không PySide6; `stream_server.py` + `main.py --tui` |
| **Máy xem stream** | `pip install -e ".[viewer]"` | `opencv-python` (HighGUI) cho `view_client.py` |
| **App + viewer** | `pip install -e ".[all]"` | Giống đầy đủ + `view_client.py` |
| **Contributor** | `pip install -e ".[dev]"` | pytest, httpx |

> **Lưu ý:** `ultralytics` kéo theo PyTorch — phần nặng nhất. Pi dùng `requirements-pi.txt` + `--no-deps` để tránh cài PySide6. `stream_server.py` chỉ cần OpenCV headless (có trong profile Pi).

```bash
cd block_detected
python3 -m venv .venv
source .venv/bin/activate          # macOS/Linux
# .\.venv\Scripts\Activate.ps1     # Windowsoy

python -m pip install --upgrade pip
```

**Desktop / dev (khuyến nghị):**

```bash
pip install -e .
```

**Raspberry Pi** (TUI + camera stream server):

```bash
pip install -r requirements-pi.txt
pip install -e . --no-deps
python stream_server.py          # trên Pi
python main.py --tui             # detection terminal trên Pi
```

**Máy xem Pi stream** (`view_client.py`):

```bash
pip install -e ".[viewer]"
# hoặc nếu đã cài app đầy đủ:
pip install -e ".[all]"
```

**Contributor** (chạy tests):

```bash
pip install -e ".[dev]"
```

### Model YOLO

Đặt weights `.pt` vào `models/` (gitignore — copy sau khi clone):

```
models/
  train-3.pt    # mặc định
  yolo26n.pt    # nhẹ hơn
```

## Chạy ứng dụng

### Cách chính — chọn GUI hoặc TUI

```bash
python main.py
```

Trong terminal tương tác sẽ hiện menu:

```
  Block Detected — chọn giao diện

    1  GUI   Desktop PySide6 (preview camera + controls)
    2  TUI   Textual dashboard (metrics trong terminal)

    q  Thoát

Chọn [1/2/q] (mặc định 1):
```

Tương đương:

```bash
python -m block_detected
block-detected
```

### Chạy trực tiếp (bỏ qua menu)

```bash
python main.py --gui          # hoặc -g, python main.py gui
python main.py --tui          # hoặc -t, python main.py tui
block-detected-gui
block-detected-tui
```

Biến môi trường (CI / script):

```bash
export BLOCK_DETECTED_UI=tui
python main.py
```

TUI nhận thêm flag runtime:

```bash
python main.py --tui --camera-index 1 --conf 0.35
block-detected-tui --config /path/to/block_detected.toml
```

### Raspberry Pi camera stream (ngoài package chính)

Trên Pi (server):

```bash
python stream_server.py
```

Trên máy xem:

```bash
python view_client.py              # cửa sổ settings (cần tkinter)
python view_client.py --host <pi-ip>   # CLI, chỉ OpenCV preview
python view_client.py --cli            # tự tìm Pi trên LAN
```

## GUI — ROBO-VISION OS (desktop)

Layout theo mockup Stitch trong `example_ui/stitch_block_pickup_vision_console/` (không cần browser).

- **START / STOP** — inference webcam
- **NEXT CAMERA / NEXT MODEL** — khi đang chạy
- **VISION PIPELINE** — accordions: PRE-PROCESSING, INFERENCE, STABILITY, EDGE DETECTION, DEFAULT CONFIG
- **Toolbar toggles** — Contours / Corners overlay (Warped Face: future)
- **PRIMARY DETECT / SYSTEM LOG** — tagged log rows + LIVE badge
- **Hot apply:** preprocess, inference (conf/IoU/max_det/agnostic), stability, classical overlays
- **Restart cần Stop → Start:** camera index/resolution, `inference.imgsz`, default model, log level
- **DELETE** — reset defaults + xóa `block_detected.toml`
- **Last model** — NEXT MODEL tự lưu `last_model_name` vào TOML; không còn field Default model
- **Multi detect** — PRIMARY DETECT hiển thị danh sách detection + progress bar
- **SAVE CONFIG** → `block_detected.toml` ở root repo

## TUI — phím tắt

| Phím | Chức năng |
|------|-----------|
| `S` | Start / Stop runtime |
| `M` | Đổi model tiếp theo |
| `C` | Đổi camera |
| `T` | Bật/tắt stability filters |
| `+` / `-` | Tăng / giảm confidence |
| `Q` / `Esc` | Thoát |

TUI hiển thị metrics và detection table; không mở cửa sổ preview OpenCV (phù hợp SSH/headless terminal).

## Cấu hình

- Mặc định: `src/block_detected/runtime/config_schema.py` → `AppConfig.defaults()`
- File tùy chọn: `block_detected.toml` (auto-load từ repo root)

Ví dụ `block_detected.toml`:

```toml
[camera]
index = 0
width = 1280
height = 720

[inference]
default_conf = 0.25
last_model_name = "train-3.pt"

[stability]
enabled = true
min_confidence = 0.3
min_box_area_px = 400
temporal_window = 5
required_stable_votes = 3
```

## Cấu trúc project

```
block_detected/
├── main.py                 # launcher GUI/TUI
├── block_detected.toml     # config tùy chọn
├── models/*.pt             # weights (gitignore)
├── stream_server.py          # Pi JPEG server
├── view_client.py            # Pi stream viewer
├── pyproject.toml
├── AGENTS.md
└── src/block_detected/
    ├── apps/
    │   ├── launcher.py     # menu GUI/TUI
    │   ├── gui/            # PySide6 Robo-Vision OS
    │   └── tui/            # Textual dashboard
    ├── runtime/            # engine, config, postprocess, metrics
    ├── detection/yolo/     # YOLO backend
    ├── vision/drawing/     # overlay, status bar
    └── io/camera/          # webcam open/switch
```

## Tests

```bash
python -m pytest tests/ -q
```

Không cần webcam thật cho hầu hết tests.

## Xử lý lỗi

**Không có model `.pt`**

- Copy weights vào `models/`, rồi Start lại (GUI/TUI).

**Camera không mở**

- Đóng app khác đang dùng camera.
- Đổi `camera.index` trong GUI/TUI hoặc TOML → Stop → Start.
- macOS: kiểm tra quyền camera trong System Settings.

**PySide6 / Textual thiếu**

```bash
pip install -e .    # desktop đầy đủ (GUI + TUI)
```

Trên Pi (không cần GUI): dùng `requirements-pi.txt` như mục Cài đặt.

**Chạy không có menu (pipe/CI)**

- Dùng `--gui` hoặc `--tui` — menu chỉ hiện khi stdin/stdout là terminal.

**`view_client.py`: No module named '_tkinter'`**

```bash
brew install python-tk@3.14    # macOS Homebrew
# hoặc bỏ qua tkinter:
python view_client.py --host <pi-ip>
```

**Inference chậm**

- Giảm resolution trong config.
- Dùng model nhỏ hơn (`yolo26n.pt`).

## Ghi chú

- [Ultralytics YOLO](https://docs.ultralytics.com/) · OpenCV · PySide6 · Textual
- Chi tiết module và quy tắc layer: [AGENTS.md](AGENTS.md)

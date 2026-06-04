# Block Detected — YOLO

Nhận diện khối/vật thể bằng YOLO (Ultralytics), điều khiển qua **GUI desktop** (PySide6).

> **Cho AI agent / contributor:** xem [AGENTS.md](AGENTS.md).

## Yêu cầu

- **Python** 3.10+
- **Webcam**
- **GPU NVIDIA** (tùy chọn)

## Cài đặt

```bash
cd block_detected
python -m venv .venv
# Windows: .\.venv\Scripts\Activate.ps1
# macOS/Linux: source .venv/bin/activate
python -m pip install --upgrade pip
pip install -e ".[dev]"
```

Hoặc: `pip install -r requirements.txt`

### Model

Đặt file `.pt` vào `models/` (gitignore — copy sau khi clone):

```
models/
  train-3.pt    # mặc định
  yolo26n.pt
```

## Chạy ứng dụng

```bash
python main.py
```

Tương đương:

```bash
python -m block_detected
block-detected
```

GUI: preview camera, confidence/eval, đổi model/camera, FPS/latency trên status bar, log. **Save TOML** → `block_detected.toml`.

Cấu hình mặc định: `runtime/config_schema.py`; file tùy chọn: `block_detected.toml` ở root repo.

## Cấu trúc

```
block_detected/
├── main.py                 # entry → GUI
├── pyproject.toml
├── models/
└── src/block_detected/
    ├── apps/gui/           # PySide6 UI
    ├── runtime/            # engine, config, metrics
    ├── detection/yolo/
    ├── vision/drawing/
    └── io/camera/
```

Chi tiết: [AGENTS.md](AGENTS.md).

## Tests

```bash
python -m pytest tests/ -q
```

## Xử lý lỗi

**PySide6 chưa cài**

```bash
pip install -e .
```

**Không có model**

- Copy `.pt` vào `models/`, rồi Start lại GUI.

**Camera không mở**

- Đóng app khác đang dùng camera; đổi camera index trong GUI hoặc TOML → **Stop** → **Start**.

**Field cần restart** (đang chạy inference)

- Camera index, resolution, default model, log level → Stop → Start.
- Hot: confidence, eval, stability filters.

## Ghi chú

- [Ultralytics YOLO](https://docs.ultralytics.com/) + OpenCV + PySide6.

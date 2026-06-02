# Block Detected — YOLO

Dự án nhận diện khối/vật thể bằng mô hình YOLO (Ultralytics), chạy **webcam realtime**.

> **Cho AI agent / contributor:** xem [AGENTS.md](AGENTS.md) để biết sửa file nào khi thay đổi config, UI, camera, model, phím tắt.

## Yêu cầu

- **Python** 3.10 trở lên (khuyến nghị 3.11+)
- **Webcam**
- **GPU NVIDIA** (tùy chọn; không bắt buộc)

## Cài đặt

### 1. Clone hoặc mở thư mục dự án

```bash
cd block_detected
```

### 2. Virtual environment (khuyến nghị)

```bash
python3 -m venv .venv
source .venv/bin/activate   # macOS/Linux
# .\.venv\Scripts\Activate.ps1   # Windows
```

### 3. Cài package

```bash
python -m pip install --upgrade pip
pip install -e ".[dev]"
```

GUI desktop dùng PySide6 là optional:

```bash
pip install -e ".[dev,gui]"
```

Hoặc chỉ runtime:

```bash
pip install -r requirements.txt
```

### 4. Chạy tests

```bash
python -m pytest tests/ -q
```

### 5. Model

Mặc định dùng `models/train-3.pt`. Đặt file `.pt` vào `models/`:

```
models/
  train-3.pt    # mặc định
  yolo26n.pt    # model nhỏ hơn (nhanh hơn)
```

File `.pt` lớn và đã gitignore — copy sau khi clone.

## Cấu trúc project (layered CV)

```
block_detected/
├── pyproject.toml
├── main.py
├── AGENTS.md                   # bản đồ chi tiết cho agent
├── models/                     # weights YOLO
└── src/block_detected/
    ├── apps/webcam/            # vòng lặp chính
    ├── apps/gui/               # GUI PySide6 optional
    ├── runtime/                # engine, config, metrics, logging
    ├── config/                 # paths, camera, inference, ui
    ├── core/                   # types dùng chung
    ├── detection/yolo/         # load model, parse boxes
    ├── vision/drawing/         # vẽ overlay, widget
    ├── io/camera/              # webcam
    └── ui/input/               # phím + chuột
```

Chi tiết “sửa ở đâu” và mở rộng sau này (tracking, video I/O, GUI): [AGENTS.md](AGENTS.md).

## Sử dụng

### Webcam OpenCV

```bash
python main.py
```

Hoặc sau `pip install -e .`:

```bash
block-detected-webcam
```

Cửa sổ **YOLO Webcam Inference** hiển thị video có bounding box.

| Phím / thao tác | Chức năng |
|-----------------|-----------|
| `q` | Thoát |
| `v` hoặc **click nút Model** (góc dưới trái) | Chuyển model tiếp theo trong `models/*.pt` |
| `c` | Chuyển camera (0 → 5) |
| `↑` / `↓` | Tăng / giảm ngưỡng confidence (chế độ normal) |
| `m` | Bật/tắt overlay lịch sử nhiều khung |
| `n` | Bật/tắt eval mode (nhãn %, conf cố định 0.01) |

### GUI desktop

Cài extra `gui`, rồi chạy:

```bash
block-detected-gui
```

GUI có preview camera, chỉnh confidence/eval/overlay, đổi model/camera, xem FPS/latency và log buffer. Nút **Save TOML** ghi cấu hình vào `block_detected.toml`.

**Cấu hình mặc định:** `runtime/config_schema.py`; file tùy chọn ở repo root: `block_detected.toml`.

## Xử lý lỗi thường gặp

**Thiếu PySide6 (GUI)**

- Triệu chứng: `block-detected-gui` in `[ERROR] PySide6 is not installed`.
- Cài: `pip install -e ".[gui]"` hoặc `pip install -e ".[dev,gui]"`.

**Không có model `.pt`**

- Triệu chứng: `No .pt models found in .../models` (CLI hoặc dialog GUI).
- Đặt file weights vào `models/` (ví dụ `train-3.pt`), rồi Start lại GUI hoặc chạy lại CLI.

**Camera permission / busy**

- Triệu chứng: `Failed to open camera index N` trong log hoặc dialog GUI.
- Đóng app khác đang dùng camera; kiểm tra quyền camera (macOS System Settings).
- Đổi **Camera index** trong GUI hoặc `block_detected.toml`, rồi **Stop → Start** (không hot-reload).

**GUI: field cần restart**

- Trong lúc inference đang chạy, các field sau **không** áp dụng ngay: camera index/max, width/height, default model name, log level.
- Chỉnh xong → **Stop** → **Start**, hoặc Save TOML và khởi động lại lần sau.
- Hot áp dụng ngay: confidence, eval mode, overlay trail, trail length, show FPS.

**`Failed to open webcam` (CLI)**

- Đóng app khác đang dùng camera.
- Sửa camera index trong `block_detected.toml` hoặc nhấn `c` để đổi nguồn.

**PyTorch / CUDA**

- `pip install -r requirements.txt` cài bản CPU.
- GPU: xem [PyTorch install](https://pytorch.org/get-started/locally/).

**Inference chậm**

- Giảm `CAMERA_WIDTH` / `CAMERA_HEIGHT` trong `config/camera.py`.
- Dùng model nhỏ hơn (ví dụ `yolo26n.pt`) trong `models/`.

## Ghi chú

- [Ultralytics YOLO](https://docs.ultralytics.com/) + OpenCV.
- Chi tiết module và “sửa ở đâu”: [AGENTS.md](AGENTS.md).

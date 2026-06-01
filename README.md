# Block Detected — YOLO

Dự án nhận diện khối/vật thể bằng mô hình YOLO (Ultralytics), hỗ trợ hai chế độ:

- **Webcam realtime** — `run_yolo_webcam.py`
- **Xử lý hàng loạt ảnh** — `batch_detect_square.py` (vẽ hộp vuông quanh detection)

## Yêu cầu

- **Python** 3.10 trở lên (khuyến nghị 3.11+)
- **Webcam** (cho chế độ realtime)
- **GPU NVIDIA** (tùy chọn, tăng tốc inference; không bắt buộc)

## Cài đặt

### 1. Clone hoặc mở thư mục dự án

```powershell
cd C:\Users\minhmice\Documents\projects\block_detected
```

### 2. Tạo virtual environment (khuyến nghị)

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
```

Trên Linux/macOS:

```bash
python3 -m venv .venv
source .venv/bin/activate
```

### 3. Cài dependencies

```powershell
python -m pip install --upgrade pip
pip install -r requirements.txt
```

Lần cài đầu có thể mất vài phút vì `ultralytics` kéo theo PyTorch và các thư viện vision.

### 4. Kiểm tra model

Mặc định dùng `models/train-3.pt`. Đảm bảo file tồn tại:

```
models/
  train-3.pt    # model đã train (bắt buộc cho mặc định)
  train-2.pt
  train.pt
  yolo26n.pt
```

Đặt các file `.pt` trong `models/`. Webcam tự quét và chuyển model; batch dùng `--model`.

## Cấu trúc thư mục

```
block_detected/
├── requirements.txt
├── run_yolo_webcam.py      # inference webcam
├── batch_detect_square.py  # inference ảnh tĩnh
├── models/                 # file .pt
├── images/                 # ảnh đầu vào (batch)
└── images_out/             # ảnh đã vẽ box (tự tạo khi chạy batch)
```

## Sử dụng

### Webcam realtime

```powershell
python run_yolo_webcam.py
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

Cấu hình trong đầu file `run_yolo_webcam.py`: độ phân giải camera, `CAMERA_INDEX`, v.v.

### Batch — xử lý thư mục ảnh

Đặt ảnh vào `images/` (`.jpg`, `.jpeg`, `.png`, `.bmp`, `.webp`), rồi chạy:

```powershell
python batch_detect_square.py
```

Kết quả lưu vào `images_out/` (cùng tên file).

**Tham số tùy chọn:**

```powershell
python batch_detect_square.py --input images --output images_out --conf 0.01 --show
```

| Tham số | Mặc định | Mô tả |
|---------|----------|--------|
| `--model` | `models/train-3.pt` | Đường dẫn model YOLO |
| `--input` | `images` | Thư mục ảnh đầu vào |
| `--output` | `images_out` | Thư mục ảnh đã annotate |
| `--conf` | `0.01` | Ngưỡng confidence |
| `--show` | (tắt) | Xem từng ảnh; nhấn phím bất kỳ để tiếp, `q` để dừng |

## Xử lý lỗi thường gặp

**`Model file not found`**

- Kiểm tra `models/train-3.pt` có tồn tại.
- Hoặc truyền `--model` trỏ tới file `.pt` hợp lệ.

**`Failed to open webcam`**

- Đóng app khác đang dùng camera.
- Thử đổi `CAMERA_INDEX` trong `run_yolo_webcam.py` hoặc nhấn `c` để đổi nguồn.

**Cài đặt PyTorch / CUDA**

- `pip install -r requirements.txt` cài bản CPU phù hợp hệ điều hành.
- GPU NVIDIA: xem [hướng dẫn PyTorch](https://pytorch.org/get-started/locally/) rồi cài `torch` tương thích trước khi chạy lại script.

**Inference chậm**

- Giảm `CAMERA_WIDTH` / `CAMERA_HEIGHT` trong `run_yolo_webcam.py`.
- Dùng model nhỏ hơn (ví dụ `models/yolo26n.pt`) với `--model`.

## Ghi chú

- Script dùng [Ultralytics YOLO](https://docs.ultralytics.com/) và OpenCV.
- File `.pt` thường lớn và đã được loại khỏi git (xem `.gitignore`). Tải hoặc copy model vào `models/` sau khi clone.

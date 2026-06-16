# Hướng dẫn Chức Năng Hiển Thị Toạ Độ và Góc Lệch

## Tổng Quan

Các chức năng mới được thêm vào ứng dụng Block Detected để hiển thị thông tin chi tiết về vị trí các block được phát hiện:

1. **Hiển thị tâm block với toạ độ XYWH (Màu Đỏ)**
2. **Hiển thị tâm camera với toạ độ XYWH (Màu Tím)**
3. **Hiển thị góc lệch từ tâm camera đến tâm block (Màu Cyan)**
4. **Gộp các block trùng lặp thành 1 khung duy nhất**
5. **Hiển thị thông tin kinematic trên panel KINEMATICS**

---

## Chi Tiết Các Chức Năng

### 1. Hiển Thị Tâm Block (DETECTION CENTER) - Màu Đỏ

**Vị trí trên GUI:**
- Hiển thị vòng tròn đỏ tại tâm mỗi block được phát hiện
- Kế bên là toạ độ XYWH (x, y, width, height)

**Định dạng:**
```
x:640 y:480 w:120 h:150
```

**Ý nghĩa:**
- `x, y`: vị trí góc trên-trái của block (pixel)
- `w`: chiều rộng block (pixel)
- `h`: chiều cao block (pixel)
- Tâm block = (x + w/2, y + h/2)

**Mã nguồn:**
- File: `src/block_detected/vision/drawing/detections.py`
- Hàm: `draw_detection_centers()`

---

### 2. Hiển Thị Tâm Camera (CAMERA CENTER) - Màu Tím/Magenta

**Vị trí trên GUI:**
- Hiển thị vòng tròn tím tại tâm camera
- Vẽ 2 đường gạch chéo (crosshair) để dễ nhận biết
- Kế bên là toạ độ XYWH của camera

**Định dạng:**
```
camera: x:960 y:540 w:1920 h:1080
```

**Ý nghĩa:**
- `x, y`: tâm camera (pixel) = (chiều_rộng/2, chiều_cao/2)
- `w`: chiều rộng frame (pixel)
- `h`: chiều cao frame (pixel)

**Mã nguồn:**
- File: `src/block_detected/vision/drawing/detections.py`
- Hàm: `draw_camera_center()`

---

### 3. Hiển Thị Góc Lệch (ANGLE OFFSET) - Màu Cyan

**Vị trí trên GUI:**
- Hiển thị dưới mỗi block được phát hiện
- Màu cyan (xanh nhạt)
- Định dạng: `angle: XX.X°`

**Ý nghĩa Góc Độ:**
- **0°**: Block ở bên phải tâm camera
- **90°**: Block ở dưới tâm camera
- **-90°**: Block ở trên tâm camera
- **180° hoặc -180°**: Block ở bên trái tâm camera

**Ví dụ:**
```
angle: 45.5°   → Block ở góc dưới-phải (45 độ so với chiều ngang)
angle: -30.2°  → Block ở góc trên-phải (30 độ so với chiều ngang)
angle: -120.0° → Block ở góc trên-trái (120 độ so với chiều ngang)
```

**Công thức tính:**
```
angle = atan2(dy, dx) * 180 / π
    với: dy = center_y_block - center_y_camera
         dx = center_x_block - center_x_camera
```

**Mã nguồn:**
- File: `src/block_detected/vision/drawing/detections.py`
- Hàm: `draw_angle_offset()`
- Helper: `src/block_detected/vision/geometry.py` - `angle_between_points()`

---

### 4. Gộp Các Block Trùng Lặp (MERGE OVERLAPPING DETECTIONS)

**Chức năng:**
- Nếu phát hiện 2 hoặc nhiều block cùng loại/giống nhau (IoU ≥ 0.3)
- Gộp chúng thành 1 khung bao quát tất cả các block này
- Sử dụng độ tin cậy (confidence) cao nhất

**Khi nào được kích hoạt:**
- Tự động trong hàm `process_frame()` của `WebcamEngine`
- Trước khi vẽ detection centers

**Ví dụ:**
```
Input:  4 block giống nhau xếp liền nhau
        ┌─────┐ ┌─────┐
        │ 85% │ │ 82% │
        └─────┘ └─────┘
        ┌─────┐ ┌─────┐
        │ 88% │ │ 80% │
        └─────┘ └─────┘

Output: 1 khung bao quát tất cả (confidence = 88%)
        ┌───────────────┐
        │ merged (88%)  │
        └───────────────┘
```

**Mã nguồn:**
- File: `src/block_detected/vision/drawing/detections.py`
- Hàm: `merge_overlapping_detections(iou_threshold=0.3)`

---

### 5. Panel KINEMATICS - Hiển Thị Thông Tin Chi Tiết

**Vị trí:**
- GUI desktop (PySide6) - panel dưới cùng bên trái
- Cạnh "PRIMARY DETECT" và "SYSTEM LOG"

**Các thông tin hiển thị:**

1. **target_status** - Trạng thái phát hiện
   - `idle`: Chưa phát hiện block nào
   - `acquired`: Đã phát hiện block

2. **center_px** - Toạ độ tâm block
   - Định dạng: `[640, 480]`
   - Cập nhật thực thời khi có block phát hiện

3. **angle_deg** - Góc lệch
   - Định dạng: `45.2°`
   - Tính từ tâm camera đến tâm block

4. **distance_px** - Khoảng cách pixel
   - Định dạng: `250.5`
   - Tính Euclidean từ tâm camera đến tâm block

5. **camera_center_px** - Toạ độ tâm camera
   - Định dạng: `[960, 540]`
   - Tùy thuộc resolution camera

**Mã nguồn:**
- File: `src/block_detected/apps/gui/widgets/kinematics_card.py`
- Class: `KinematicsCard`
- Hàm: `update_status(status)`

---

## Tích Hợp Hệ Thống

### Luồng Dữ Liệu

```
Frame từ Camera
    ↓
[Inference - YOLO]
    ↓
[Detections]
    ↓
[Merge Overlapping] ← Gộp block trùng lặp
    ↓
[Render/Draw]
    ├─ draw_detection_boxes() (bounding box xanh lá)
    ├─ draw_detection_centers() (tâm đỏ + XYWH)
    ├─ draw_camera_center() (tâm tím + crosshair)
    └─ draw_angle_offset() (góc lệch cyan)
    ↓
[Calculate Kinematics]
    ├─ primary_center_px
    ├─ primary_angle_deg
    └─ camera_center_px
    ↓
[RuntimeStatus]
    ↓
[GUI Update]
    ├─ KINEMATICS panel
    ├─ PRIMARY DETECT panel
    └─ Preview viewport
```

### Files Liên Quan

| File | Chức Năng |
|------|----------|
| `vision/geometry.py` | Helper: tâm, XYWH, góc, khoảng cách |
| `vision/drawing/detections.py` | Vẽ tâm block, tâm camera, góc lệch, merge |
| `runtime/engine.py` | Tính toán kinematic, gọi vẽ |
| `core/domain.py` | RuntimeStatus + kinematic fields |
| `apps/gui/widgets/kinematics_card.py` | GUI panel hiển thị |
| `apps/gui/robo_window.py` | Kết nối signal/slot |

---

## Cách Sử Dụng

### Chạy Ứng Dụng

```bash
# Chạy GUI desktop
python main.py --gui

# Hoặc interactive menu
python main.py
# → Chọn [1] GUI
```

### Quan Sát Các Chức Năng

1. **Start detection** bằng nút START
2. Hướng camera vào các block
3. Quan sát:
   - **Viewport**: tâm block (đỏ), tâm camera (tím), góc lệch (cyan)
   - **KINEMATICS panel**: thông tin chi tiết

### Tùy Chỉnh Hành Vi

**Merge threshold** (trong `runtime/engine.py`):
```python
merged_detections = merge_overlapping_detections(
    frame_result.detections,
    iou_threshold=0.3,  # ← Thay đổi giá trị này
)
```

- **0.0 - 0.3**: Gộp nhiều (hợp nhất sớm)
- **0.3 - 0.5**: Cân bằng (mặc định)
- **0.5 - 1.0**: Gộp ít (chỉ gộp khi trùng lặp lớn)

---

## Tham Khảo Thêm

- **AGENTS.md**: Quy tắc cấu trúc project
- **README.md**: Hướng dẫn chạy tổng quát
- Các hàm helper trong `vision/geometry.py`
- Thử `python -m pytest tests/test_geometry.py -xvs`

---

## Ghi Chú

- Tất cả toạ độ tính bằng **pixel**
- Góc độ tính bằng **độ (degree)**, từ **-180° đến 180°**
- Khoảng cách tính theo **Euclidean distance**
- Merge sử dụng **IoU (Intersection over Union)**
- Confidence cao nhất được giữ khi gộp block


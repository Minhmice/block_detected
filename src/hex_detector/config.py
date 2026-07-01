"""Cấu hình tập trung cho hex_detector — mọi số magic nằm ở đây."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass
class HexDetectorConfig:
    """Toàn bộ tham số có thể chỉnh của pipeline detect mặt block.

    Mỗi field tương ứng một bước trong luồng:
    YOLO bbox → crop ROI → tiền xử lý ảnh → tìm line → nhóm line →
    ghép candidate → validate → chấm điểm → (tuỳ chọn) giữ kết quả cũ.

    Gợi ý khi tune:
    - Detection quá ít / reject nhiều: hạ ngưỡng Canny/Hough, nới góc nhóm line.
    - Nhiễu / line sai nhiều: tăng Canny, tăng min_line_length, siết score threshold.
    - Chậm trên Pi: giảm max_*_candidates, tắt verbose debug.
  """

    # -------------------------------------------------------------------------
    # ROI / BBOX — vùng cắt quanh bbox YOLO
    # -------------------------------------------------------------------------

    # Tỷ lệ mở rộng bbox trước khi crop (0.08 = thêm 8% mỗi cạnh).
    # Giúp không cắt mất mép block khi YOLO bbox hơi chật.
    # Tăng nếu mép block hay bị cắt; giảm nếu ROI lấy quá nhiều nền/pallet.
    bbox_padding_ratio: float = 0.08

    # Hệ số làm mượt bbox theo thời gian (EMA).
    # 0.35 = frame mới chiếm 35%, lịch sử 65% → bbox ít giật giữa các frame.
    # Tăng (gần 1) = phản ứng nhanh hơn; giảm = mượt hơn nhưng trễ khi block di chuyển.
    bbox_ema_alpha: float = 0.35

    # Danh sách tỷ lệ cắt đáy ROI (pallet / sàn) — pipeline thử từng ratio,
    # chọn candidate có score tốt nhất. 0.0 = không cắt.
    block_crop_bottom_ratios: tuple[float, ...] = (0.0, 0.1, 0.18, 0.22)

    # Giới hạn số ratio được thử (None = thử hết list).
    max_crop_ratio_attempts: int = 4

    # -------------------------------------------------------------------------
    # TIỀN XỬ LÝ ẢNH — Gray → CLAHE → Blur → Canny → đóng morphology
    # -------------------------------------------------------------------------

    # CLAHE: giới hạn độ tương phản cục bộ (càng cao = tương phản mạnh hơn).
    # Ảnh tối / thiếu sáng: thử 2.0–3.0. Ảnh nhiễu: hạ xuống 1.5–2.0.
    clahe_clip_limit: float = 2.0

    # CLAHE chia ảnh thành lưới ô (8×8 pixel mỗi ô) để cân bằng sáng cục bộ.
    # Ô nhỏ hơn (4×4) = chi tiết hơn nhưng dễ nhiễu; ô lớn hơn = mượt hơn.
    clahe_tile_grid_size: tuple[int, int] = (8, 8)

    # Kernel Gaussian blur trước Canny — làm mịn nhiễu nhỏ.
    # (5,5) là mặc định an toàn; (3,3) giữ cạnh sắc hơn, (7,7) mịn hơn.
    gaussian_kernel: tuple[int, int] = (5, 5)

    # Độ lệch chuẩn Gaussian — càng lớn blur càng mạnh.
    gaussian_sigma: float = 1.2

    # Canny: ngưỡng dưới / trên cho biên cạnh.
    # Thấp hơn → nhiều cạnh (dễ nhiễu); cao hơn → ít cạnh (có thể mất line block).
    # Thường chỉnh cặp low/high cùng lúc, tỷ lệ ~1:2 hoặc 1:3.
    canny_low: int = 40
    canny_high: int = 120

    # Morphology close: nối các đoạn cạnh đứt đoạn thành line liền hơn.
    # kernel 3×3, 1 lần lặp — đủ cho block có viền đỏ rõ.
    morph_kernel_size: int = 3
    morph_iterations: int = 1

    # -------------------------------------------------------------------------
    # HOUGH LINES P — tìm đoạn thẳng từ ảnh biên
    # -------------------------------------------------------------------------

    # Độ phân giải khi quét Hough (pixel) — 1.0 = mỗi pixel một bước.
    hough_rho: float = 1.0

    # Bước góc quét (độ) — 1° là đủ cho block hơi nghiêng.
    hough_theta_deg: float = 1.0

    # Số vote tối thiểu để chấp nhận một line.
    # Cao hơn → ít line hơn, chắc hơn; thấp hơn → nhiều line, dễ nhiễu.
    hough_threshold: int = 30

    # Độ dài line tối thiểu = tỷ lệ cạnh ngắn ROI (0.12 = 12%).
    # Line ngắn hơn bị bỏ (nhiễu, vết xước).
    hough_min_line_length_ratio: float = 0.12

    # Khoảng trống tối đa giữa hai đoạn cùng line để Hough gộp thành một.
    hough_max_line_gap: int = 8

    # -------------------------------------------------------------------------
    # LỌC LINE — bỏ line ngắn, sát biên ROI, line pallet
    # -------------------------------------------------------------------------

    # Độ dài tối thiểu tuyệt đối (pixel) — dưới ngưỡng này luôn bỏ.
    min_line_length_px: int = 18

    # Lề an toàn mép ROI (tỷ lệ) — line có tâm nằm trong vùng lề bị coi là
    # line sát biên (thường là artifact crop), không dùng cho geometry.
    roi_edge_margin_ratio: float = 0.04

    # Phần dưới ROI (từ 55% chiều cao trở xuống) — line gần ngang ở đây
    # thường là thanh pallet, bỏ qua.
    pallet_line_bottom_ratio: float = 0.55

    # Dung sai góc (độ) để coi line là “ngang pallet” (gần 0° hoặc 180°).
    pallet_line_angle_tol_deg: float = 12.0

    # -------------------------------------------------------------------------
    # NHÓM LINE THEO GÓC — chia 3 loại cho topology A–F
    #
    #   vertical (đứng ~90°):     cạnh AF, BE, CD
    #   front_horizontal (~0°):   cạnh AB, FE (mặt trước)
    #   right_diagonal (~55°):    cạnh BC, ED (mặt phải)
    # -------------------------------------------------------------------------

    # Góc chuẩn của nhóm “đứng” (độ, chuẩn hoá 0–180).
    vertical_angle_center: float = 90.0

    # Line lệch tối đa bao nhiêu độ so với 90° vẫn được xếp vào vertical.
    vertical_angle_tol_deg: float = 22.0

    # Dung sai góc cho cạnh ngang mặt trước (AB, FE) — quanh 0°.
    front_horizontal_angle_tol_deg: float = 28.0

    # Dung sai góc cho cạnh chéo mặt phải (BC, ED) — quanh 55°.
    right_diagonal_angle_tol_deg: float = 35.0

    # Góc mục tiêu mặt trước (thường 0° = ngang).
    front_horizontal_target_deg: float = 0.0

    # Góc mục tiêu mặt phải (chéo ~55° tùy góc camera).
    right_diagonal_target_deg: float = 55.0

    # -------------------------------------------------------------------------
    # GỘP LINE — merge các line gần song song, gần vị trí
    # -------------------------------------------------------------------------

    # Hai line lệch góc ≤ ngưỡng này (độ) có thể gộp thành một.
    merge_angle_tol_deg: float = 8.0

    # Khoảng cách vị trí tối đa (tỷ lệ cạnh ROI) để gộp line cùng nhóm.
    merge_distance_tol_ratio: float = 0.06

    # Sau merge, mỗi nhóm giữ tối đa bao nhiêu line (tránh bùng candidate).
    max_lines_per_group: int = 6

    # -------------------------------------------------------------------------
    # TÌM CANDIDATE — ghép tổ hợp line rồi tính giao điểm A–F
    # -------------------------------------------------------------------------

    # Giới hạn candidate cho mặt trước (AF, BE, AB, FE) — chỉ cần 2 dọc + 2 ngang.
    # Pi chậm: giảm xuống 12–16.
    max_front_candidates: int = 24

    # Giới hạn candidate nâng cấp hex (CD, BC, ED) sau khi đã có rectangle.
    max_right_candidates: int = 24

    # -------------------------------------------------------------------------
    # VALIDATE — kiểm tra topology trước khi chấp nhận
    # -------------------------------------------------------------------------

    # Diện tích tứ giác mặt trước (A-B-E-F) tối thiểu so với ROI.
    # Quá nhỏ = candidate vô lý / nhiễu.
    min_front_area_ratio: float = 0.08

    # Chiều rộng mặt phải (C.x - B.x) tối thiểu so với ROI để chấp hex.
    min_right_width_ratio: float = 0.06

    # Nếu mặt phải hẹp hơn ngưỡng này → chế độ rectangle (chỉ A,B,E,F).
    # Không tạo C,D giả khi mặt phải quá hẹp.
    rectangle_mode_right_width_ratio: float = 0.10

    # Hai cạnh được coi “song song” nếu lệch góc ≤ ngưỡng này (độ).
    parallel_tol_deg: float = 12.0

    # Cho phép điểm lệch ra ngoài ROI thêm vài pixel (do làm tròn / nhiễu).
    point_inside_margin_px: int = 2

    # -------------------------------------------------------------------------
    # CHẤM ĐIỂM — trọng số phải cộng = 1.0
    #
    # Candidate tốt nhất được chọn theo tổng điểm; dưới accept_score_threshold
    # → reject (not_detected).
    # -------------------------------------------------------------------------

    # 40% — điểm A–F có nằm trên biên Canny không (edge support).
    weight_edge_support: float = 0.40

    # 20% — các cạnh AF∥BE∥CD, AB∥FE, BC∥ED có song song không.
    weight_parallelism: float = 0.20

    # 20% — thứ tự x, lồi, trên/dưới đúng topology không.
    weight_topology: float = 0.20

    # 10% — diện tích / vị trí mặt trước hợp lý trong ROI.
    weight_area_position: float = 0.10

    # 10% — gần với kết quả frame trước (ổn định theo track).
    weight_temporal: float = 0.10

    # Tổng điểm tối thiểu để accept (0–1). Cao hơn = khó detect hơn, ít false positive.
    accept_score_threshold: float = 0.52

    # Riêng edge support phải đạt tối thiểu này, dù tổng điểm cao.
    # Chặn candidate “đẹp trên giấy” nhưng không bám biên thật.
    min_edge_support_score: float = 0.15

    # -------------------------------------------------------------------------
    # THEO DÕI THEO THỜI GIAN — EMA điểm + giữ kết quả cũ khi mất detection
    # -------------------------------------------------------------------------

    # Làm mượt tọa độ A–F theo track_id (EMA điểm).
    point_ema_alpha: float = 0.45

    # Giữ kết quả tốt cuối tối đa bao nhiêu frame khi CV/YOLO tạm mất.
    max_hold_frames: int = 3

    # IoU bbox hiện tại vs bbox lúc detect thành công phải ≥ 0.5 mới được hold.
    # Tránh giữ geometry của object khác khi tracker đổi ID / nhảy bbox.
    hold_iou_threshold: float = 0.5

    # Mỗi frame hold, score nhân thêm hệ số này: score *= 0.8^hold_age.
    # Frame 1: 0.8, frame 2: 0.64, frame 3: 0.512 — thể hiện độ tin cậy giảm dần.
    hold_score_decay: float = 0.8

    # Tâm bbox nhảy quá tỷ lệ này (so với kích thước bbox) → không hold.
    hold_bbox_center_jump_ratio: float = 0.3

    # Kích thước bbox đổi quá tỷ lệ này (rộng/cao) → không hold.
    hold_bbox_size_change_ratio: float = 0.5

    # Điểm mới conflict mạnh với điểm cũ (chuẩn hoá theo ROI) → không hold.
    hold_point_conflict_threshold: float = 0.3

    # -------------------------------------------------------------------------
    # DEBUG / HIỂN THỊ
    # -------------------------------------------------------------------------

    # Vẽ mọi line thô từ Hough (màu xám) — chỉ khi renderer bật tương ứng.
    debug_draw_raw_lines: bool = True

    # Vẽ line đã chọn theo nhóm (vertical / front / right).
    debug_draw_selected_lines: bool = True

    # "basic" = chỉ bbox + geometry thắng + điểm + score (nhẹ cho Pi).
    # "verbose" = thêm grouped lines + top candidate (tốn CPU hơn).
    debug_mode: str = "basic"

    # Ở verbose, lưu/hiển thị tối đa bao nhiêu candidate cao điểm.
    debug_top_candidates: int = 5

    # Ghi log phân loại line (góc, nhóm, angular error) qua logging DEBUG.
    line_group_log_enabled: bool = False

    def validate(self) -> None:
        """Kiểm tra cấu hình hợp lệ — gọi khi khởi tạo HexDetector."""
        total = (
            self.weight_edge_support
            + self.weight_parallelism
            + self.weight_topology
            + self.weight_area_position
            + self.weight_temporal
        )
        if abs(total - 1.0) > 1e-6:
            raise ValueError(f"Trọng số score phải cộng = 1.0, hiện tại = {total}")
        if not self.block_crop_bottom_ratios:
            raise ValueError("block_crop_bottom_ratios không được rỗng")
        for ratio in self.block_crop_bottom_ratios:
            if not 0.0 <= ratio < 1.0:
                raise ValueError(
                    f"block_crop_bottom_ratios phải trong [0, 1), hiện tại = {ratio}"
                )
        if self.max_crop_ratio_attempts <= 0:
            raise ValueError(
                f"max_crop_ratio_attempts phải > 0, hiện tại = {self.max_crop_ratio_attempts}"
            )
        if self.max_front_candidates <= 0:
            raise ValueError(
                f"max_front_candidates phải > 0, hiện tại = {self.max_front_candidates}"
            )
        if self.max_right_candidates <= 0:
            raise ValueError(
                f"max_right_candidates phải > 0, hiện tại = {self.max_right_candidates}"
            )
        if not 0.0 <= self.min_edge_support_score <= 1.0:
            raise ValueError(
                f"min_edge_support_score phải trong [0, 1], hiện tại = {self.min_edge_support_score}"
            )
        if not 0.0 <= self.accept_score_threshold <= 1.0:
            raise ValueError(
                f"accept_score_threshold phải trong [0, 1], hiện tại = {self.accept_score_threshold}"
            )
        if not 0.0 <= self.hold_iou_threshold <= 1.0:
            raise ValueError(
                f"hold_iou_threshold phải trong [0, 1], hiện tại = {self.hold_iou_threshold}"
            )
        if not 0.0 < self.hold_score_decay < 1.0:
            raise ValueError(
                f"hold_score_decay phải trong (0, 1), hiện tại = {self.hold_score_decay}"
            )
        if self.max_hold_frames <= 0:
            raise ValueError(
                f"max_hold_frames phải > 0, hiện tại = {self.max_hold_frames}"
            )
        if self.debug_mode not in ("basic", "verbose"):
            raise ValueError(
                f"debug_mode phải là 'basic' hoặc 'verbose', hiện tại = {self.debug_mode}"
            )
        if self.debug_top_candidates <= 0:
            raise ValueError(
                f"debug_top_candidates phải > 0, hiện tại = {self.debug_top_candidates}"
            )


# Cấu hình mặc định — dùng khi không truyền config tùy chỉnh.
DEFAULT_CONFIG = HexDetectorConfig()

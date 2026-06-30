# Phase 1: Core CV Pipeline - Discussion Log

> **Audit trail only.** Do not use as input to planning, research, or execution agents.
> Decisions are captured in CONTEXT.md — this log preserves the alternatives considered.

**Date:** 2026-06-30
**Phase:** 1-Core CV Pipeline
**Areas discussed:** Rectangle fallback, Hold kết quả cũ, API và output, Debug và score

---

## Rectangle fallback

| Option | Description | Selected |
|--------|-------------|----------|
| Hex-first downgrade | Yêu cầu đủ A-F trước, sau đó bỏ C,D khi mặt phải hẹp | |
| Front-first upgrade | Detect A,B,E,F độc lập rồi nâng cấp thành hex khi mặt phải đủ support | ✓ |

**User's choice:** Front-first upgrade.
**Notes:** Front hợp lệ + right thiếu support → rectangle; front + right hợp lệ → hex; front không hợp lệ → not_detected. Không dựng C,D giả.

---

## Hold kết quả cũ

| Option | Description | Selected |
|--------|-------------|----------|
| YOLO-miss only | Chỉ giữ kết quả khi track biến mất khỏi input frame | |
| Guarded CV/YOLO hold | Hold cả CV fail và YOLO miss, có IoU/age/jump/conflict guard | ✓ |

**User's choice:** Guarded CV/YOLO hold.
**Notes:** Cùng track_id, IoU >= 0.5, tối đa 3 frame, score nhân 0.8 mỗi frame; không hold khi có dấu hiệu đổi object hoặc geometry mới mâu thuẫn mạnh.

---

## API và output

| Option | Description | Selected |
|--------|-------------|----------|
| Dict-oriented API | Input/output linh hoạt bằng dict, ít type contract | |
| Typed dataclass API | Public detect_frame, internal detect_roi, dataclass xuyên suốt | ✓ |

**User's choice:** Typed dataclass API.
**Notes:** Geometry giữ float; render đổi int. Output thêm status detected/held/rejected và reject_reason code ổn định.

---

## Debug và score

| Option | Description | Selected |
|--------|-------------|----------|
| Single verbose overlay | Luôn vẽ grouped lines và thông tin chi tiết | |
| Basic/verbose split | Basic chỉ candidate thắng; verbose thêm grouped lines và top candidates | ✓ |

**User's choice:** Basic/verbose split với score breakdown bắt buộc.
**Notes:** Breakdown gồm edge_support, parallelism, topology, area_position, temporal, total. Không render mọi line mặc định để tránh rối và giảm tải Pi 5.

---

## the agent's Discretion

- Ngưỡng bbox jump và geometry conflict cụ thể.
- Số top candidates trong verbose debug.
- Tên dataclass kết quả cuối cùng nếu cần đổi từ `DetectionResult` sang `HexResult`.

## Deferred Ideas

None.

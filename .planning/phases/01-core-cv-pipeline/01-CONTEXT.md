# Phase 1: Core CV Pipeline - Context

**Gathered:** 2026-06-30
**Status:** Ready for planning

<domain>
## Phase Boundary

Hoàn thiện module độc lập `src/hex_detector/` để nhận một frame cùng các YOLO bbox đã có `track_id`, phát hiện mặt trước A-B-E-F, tùy support của mặt phải mà trả topology `rectangle` hoặc `hex` A-F, và trả `not_detected` khi mặt trước không hợp lệ. Phase này không thay đổi YOLO/tracker bên ngoài module và không đọc hay phụ thuộc code `block_detected` cũ.

</domain>

<decisions>
## Implementation Decisions

### Rectangle fallback
- **D-01:** Rectangle phải được phát hiện độc lập từ front quadrilateral A,B,E,F; pipeline không được yêu cầu tìm C,D trước.
- **D-02:** Pipeline phân nhánh theo thứ tự: front hợp lệ nhưng right face thiếu support → `rectangle`; front + right hợp lệ → `hex`; front không hợp lệ → `not_detected`.
- **D-03:** Không bao giờ nội suy hoặc dựng C,D giả. Với `rectangle`, C và D phải là `None`.

### Temporal hold
- **D-04:** Hold last-good result cả khi `track_id` vẫn còn nhưng CV fail và khi YOLO miss tạm thời.
- **D-05:** Chỉ hold khi cùng `track_id`, bbox IoU >= 0.5, `hold_age <= 3` frame, và không có bbox jump lớn.
- **D-06:** Mỗi frame hold nhân score hiện tại với `0.8`; output phải phân biệt `status: detected | held | rejected`.
- **D-07:** Không hold cho track mới, IoU thấp, bbox có dấu hiệu đổi object, hoặc detection mới mâu thuẫn mạnh với last-good result.

### API and output contract
- **D-08:** Public API là `HexDetector.detect_frame(frame: np.ndarray, detections: Sequence[YoloDetection]) -> list[HexResult]`.
- **D-09:** Detection trên một ROI là API nội bộ: `detect_roi(frame, bbox, track_id) -> HexResult`.
- **D-10:** Dùng dataclass/type rõ ràng xuyên suốt nội bộ; không truyền dict nội bộ. Tọa độ geometry giữ dạng `float` và chỉ đổi sang `int` khi render.
- **D-11:** `reject_reason` dùng code ổn định. Tập code tối thiểu: `NO_LINES`, `NO_FRONT_FACE`, `INVALID_TOPOLOGY`, `LOW_EDGE_SUPPORT`, `LOW_SCORE`, `ROI_EMPTY`.

### Debug and scoring
- **D-12:** Có hai mức debug: `debug_basic` chỉ chứa candidate thắng, các điểm và score; `debug_verbose` bổ sung toàn bộ grouped lines và top candidates.
- **D-13:** Mọi kết quả detection phải có score breakdown gồm `edge_support`, `parallelism`, `topology`, `area_position`, `temporal`, và `total`.
- **D-14:** Mặc định không render mọi line; basic mode ưu tiên candidate thắng để overlay rõ và giảm tải trên Raspberry Pi 5.

### the agent's Discretion
- Chọn ngưỡng cụ thể để định nghĩa “bbox jump lớn” và “detection mâu thuẫn mạnh”, nhưng phải cấu hình được và tuân thủ IoU tối thiểu 0.5.
- Chọn số lượng top candidates giữ trong `debug_verbose` và cách biểu diễn typed debug payload.
- Chọn tên class kết quả cuối cùng (`HexResult` hoặc đổi tên tương đương) miễn public contract nhất quán và không dùng dict nội bộ.

</decisions>

<canonical_refs>
## Canonical References

**Downstream agents MUST read these before planning or implementing.**

### Project scope and requirements
- `.planning/PROJECT.md` — Core value, greenfield boundary, CPU/OpenCV constraints, and topology definitions.
- `.planning/REQUIREMENTS.md` — Phase requirements PIPE-01..10, MODE-01..03, OUT-01, DBG-01, and CFG-01.
- `.planning/ROADMAP.md` — Phase 1 goal, MVP mode, success criteria, and requirement mapping.

No external specs or ADRs were referenced during discussion.

</canonical_refs>

<code_context>
## Existing Code Insights

### Reusable Assets
- `src/hex_detector/config.py`: Central `HexDetectorConfig` already owns ROI, preprocessing, Hough, grouping, validation, scoring, temporal, and debug knobs.
- `src/hex_detector/models.py`: Typed dataclasses already exist for bbox, YOLO input, lines, points, result, and grouped lines.
- `src/hex_detector/preprocessing.py`: ROI crop and Gray → CLAHE → GaussianBlur → Canny → morph-close pipeline is already isolated and reusable.
- `src/hex_detector/geometry.py`: Intersection, topology validation, and five scoring components already exist and can be separated into front/right branches.
- `src/hex_detector/tracker.py`: EMA bbox/point state and last-good result storage provide the base for guarded hold behavior.
- `src/hex_detector/renderer.py`: Rendering already converts float coordinates to integer pixels and can be split into basic/verbose views.

### Established Patterns
- `src/hex_detector/detector.py` orchestrates preprocessing → line extraction → grouping → candidates → validation → scoring → temporal state.
- Current candidate generation in `src/hex_detector/lines.py` requires three vertical, two front-horizontal, and two right-diagonal lines. This hex-first constraint must be split so the front face can succeed independently.
- Current `score_candidate()` returns only a weighted total even though component functions are separate; the plan should preserve these functions while exposing a typed breakdown.
- Current hold logic runs only for absent active IDs. It must also handle present-track CV rejection, and frame aging must have one authoritative increment path.

### Integration Points
- `HexDetector.detect_frame()` remains the public batch entry point.
- The current private `_detect_one()` is the natural extraction point for the internal `detect_roi()` contract.
- `DetectionResult`/successor is the boundary shared by detector, tracker, renderer, and callers.

</code_context>

<specifics>
## Specific Ideas

- Treat front-face detection as the base result and right-face evidence as an optional upgrade to hex.
- Apply multiplicative score decay `score *= 0.8` for each held frame.
- Keep stable machine-readable rejection codes rather than free-form explanations.
- Optimize default debug output for a Pi 5: render only the winning geometry unless verbose mode is explicitly enabled.

</specifics>

<deferred>
## Deferred Ideas

None — discussion stayed within phase scope.

</deferred>

---

*Phase: 1-Core CV Pipeline*
*Context gathered: 2026-06-30*

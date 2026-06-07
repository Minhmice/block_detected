"""Post-processing and temporal stability (no camera/model)."""

from block_detected.core.domain import Detection
from block_detected.runtime.config_schema import StabilityConfig
from block_detected.runtime.postprocess import (
    DetectionPostProcessor,
    TemporalStabilityTracker,
    filter_edge_boxes,
    filter_min_area,
    filter_min_confidence,
    merge_duplicate_detections,
)
from block_detected.vision.geometry import box_area, iou


def _det(
    box: tuple[int, int, int, int],
    *,
    confidence: float = 0.9,
    class_id: int = 0,
    class_name: str = "block",
) -> Detection:
    return Detection(
        box=box,
        class_id=class_id,
        class_name=class_name,
        confidence=confidence,
    )


def test_iou_identical_boxes():
    box = (10, 10, 50, 50)
    assert iou(box, box) == 1.0


def test_iou_disjoint_boxes():
    assert iou((0, 0, 10, 10), (20, 20, 30, 30)) == 0.0


def test_box_area():
    assert box_area((0, 0, 10, 20)) == 200


def test_filter_min_confidence_rejects_low_scores():
    detections = [_det((0, 0, 10, 10), confidence=0.2), _det((20, 20, 40, 40), confidence=0.8)]
    kept = filter_min_confidence(detections, 0.5)
    assert len(kept) == 1
    assert kept[0].confidence == 0.8


def test_filter_min_area_rejects_small_boxes():
    detections = [_det((0, 0, 5, 5)), _det((0, 0, 20, 20))]
    kept = filter_min_area(detections, 100)
    assert len(kept) == 1
    assert box_area(kept[0].box) >= 100


def test_filter_edge_boxes_rejects_partial_detections():
    detections = [
        _det((0, 0, 40, 40)),
        _det((50, 50, 120, 120)),
    ]
    kept = filter_edge_boxes(detections, frame_width=200, frame_height=200, margin_px=2)
    assert len(kept) == 1
    assert kept[0].box == (50, 50, 120, 120)


def test_merge_duplicate_detections_keeps_highest_confidence():
    detections = [
        _det((10, 10, 50, 50), confidence=0.6),
        _det((12, 12, 52, 52), confidence=0.95),
        _det((200, 200, 240, 240), confidence=0.8),
    ]
    merged = merge_duplicate_detections(detections, iou_threshold=0.5)
    assert len(merged) == 2
    assert max(d.confidence for d in merged if d.box[0] < 100) == 0.95


def test_temporal_stability_requires_votes_across_window():
    tracker = TemporalStabilityTracker(window=5, required_votes=3, match_iou=0.5)
    stable_box = (100, 100, 140, 140)
    flicker_box = (10, 10, 30, 30)

    for _ in range(2):
        assert tracker.update([_det(flicker_box, confidence=0.9)]) == []

    stable = tracker.update([_det(stable_box, confidence=0.9)])
    assert stable == []

    for _ in range(2):
        out = tracker.update([_det(stable_box, confidence=0.9)])
    assert len(out) == 1
    assert out[0].box == stable_box


def test_detection_post_processor_disabled_passthrough():
    processor = DetectionPostProcessor(StabilityConfig(enabled=False))
    detections = [_det((0, 0, 10, 10), confidence=0.1)]
    assert processor.process(detections, frame_width=640, frame_height=480) == detections


def test_detection_post_processor_full_pipeline():
    config = StabilityConfig(
        enabled=True,
        min_confidence=0.5,
        min_box_area_px=400,
        reject_edge_boxes=True,
        duplicate_merge_iou=0.5,
        temporal_window=3,
        required_stable_votes=2,
    )
    processor = DetectionPostProcessor(config)
    target = (80, 80, 120, 120)

    first = processor.process(
        [
            _det((0, 0, 20, 20), confidence=0.9),
            _det(target, confidence=0.9),
        ],
        frame_width=200,
        frame_height=200,
    )
    assert first == []

    second = processor.process([_det(target, confidence=0.9)], frame_width=200, frame_height=200)
    assert len(second) == 1
    assert second[0].box == target


def test_update_config_rebuilds_tracker_on_temporal_change():
    config = StabilityConfig(
        enabled=True,
        min_confidence=0.0,
        min_box_area_px=0,
        reject_edge_boxes=False,
        temporal_window=3,
        required_stable_votes=2,
    )
    processor = DetectionPostProcessor(config)
    target = (80, 80, 120, 120)
    processor.process([_det(target)], frame_width=200, frame_height=200)
    stable = processor.process([_det(target)], frame_width=200, frame_height=200)
    assert len(stable) == 1

    rebuilt = StabilityConfig(
        enabled=True,
        min_confidence=0.0,
        min_box_area_px=0,
        reject_edge_boxes=False,
        temporal_window=5,
        required_stable_votes=2,
    )
    processor.update_config(rebuilt)
    assert processor.process([_det(target)], frame_width=200, frame_height=200) == []


def test_update_config_disable_resets_history():
    config = StabilityConfig(
        enabled=True,
        min_confidence=0.0,
        min_box_area_px=0,
        reject_edge_boxes=False,
        temporal_window=3,
        required_stable_votes=2,
    )
    processor = DetectionPostProcessor(config)
    target = (80, 80, 120, 120)
    processor.process([_det(target)], frame_width=200, frame_height=200)
    processor.process([_det(target)], frame_width=200, frame_height=200)

    disabled = StabilityConfig(
        enabled=False,
        temporal_window=3,
        required_stable_votes=2,
    )
    processor.update_config(disabled)
    reenabled = StabilityConfig(
        enabled=True,
        min_confidence=0.0,
        min_box_area_px=0,
        reject_edge_boxes=False,
        temporal_window=3,
        required_stable_votes=2,
    )
    processor.update_config(reenabled)
    assert processor.process([_det(target)], frame_width=200, frame_height=200) == []


def test_update_config_min_confidence_only_preserves_tracker():
    config = StabilityConfig(
        enabled=True,
        min_confidence=0.0,
        min_box_area_px=0,
        reject_edge_boxes=False,
        temporal_window=3,
        required_stable_votes=2,
    )
    processor = DetectionPostProcessor(config)
    target = (80, 80, 120, 120)
    processor.process([_det(target)], frame_width=200, frame_height=200)
    processor.process([_det(target)], frame_width=200, frame_height=200)

    hotter = StabilityConfig(
        enabled=True,
        min_confidence=0.1,
        min_box_area_px=0,
        reject_edge_boxes=False,
        temporal_window=3,
        required_stable_votes=2,
    )
    processor.update_config(hotter)
    still_stable = processor.process([_det(target, confidence=0.9)], frame_width=200, frame_height=200)
    assert len(still_stable) == 1


def test_filter_min_confidence_empty_input():
    assert filter_min_confidence([], 0.5) == []

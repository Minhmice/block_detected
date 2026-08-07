from __future__ import annotations

import pytest

from block_detected.core.domain import Detection
from block_detected.targeting import select_target


def _detection(
    box=(0, 0, 20, 20),
    *,
    class_id=0,
    class_name="block",
    confidence=0.5,
    angle=0.0,
):
    return Detection(
        box=box,
        class_id=class_id,
        class_name=class_name,
        confidence=confidence,
        angle=angle,
    )


def test_empty_detections_return_no_target():
    assert select_target([], frame_width=100, frame_height=100) is None


def test_highest_confidence_matching_class_wins():
    detections = [
        _detection(class_id=1, class_name="person", confidence=0.8),
        _detection(class_id=2, class_name="block", confidence=0.9),
        _detection(class_id=2, class_name="block", confidence=0.7),
    ]

    target = select_target(detections, frame_width=100, frame_height=100, class_filter="BLOCK")

    assert target is not None
    assert target.class_id == 2
    assert target.confidence == 0.9


def test_class_id_filter_is_supported():
    detections = [_detection(class_id=1), _detection(class_id=2, confidence=0.8)]
    target = select_target(detections, frame_width=100, frame_height=100, class_filter=2)
    assert target is not None
    assert target.class_id == 2


def test_centered_box_has_zero_error_and_json_shape():
    target = select_target(
        [_detection(box=(40, 30, 60, 70), angle=0.25)],
        frame_width=100,
        frame_height=100,
    )

    assert target is not None
    assert target.center_px == (50.0, 50.0)
    assert target.error_px == (0.0, 0.0)
    assert target.center_norm == (0.5, 0.5)
    assert target.error_norm == (0.0, 0.0)
    assert target.to_dict()["angle"] == 0.25


def test_off_center_error_sign_and_scale():
    target = select_target([_detection(box=(70, 0, 90, 20))], frame_width=100, frame_height=100)

    assert target is not None
    assert target.error_px == (30.0, -40.0)
    assert target.error_norm == pytest.approx((0.6, -0.8))


@pytest.mark.parametrize("width,height", [(0, 100), (100, 0), (-1, 100)])
def test_invalid_frame_dimensions_are_rejected(width, height):
    with pytest.raises(ValueError, match="positive"):
        select_target([], frame_width=width, frame_height=height)

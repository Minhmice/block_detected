"""Tests for vision.geometry."""

from block_detected.vision.geometry import point_in_rect


def test_point_in_rect_inside():
    assert point_in_rect(5, 5, (0, 0, 10, 10)) is True


def test_point_in_rect_outside():
    assert point_in_rect(15, 5, (0, 0, 10, 10)) is False


def test_point_in_rect_on_edge():
    assert point_in_rect(0, 0, (0, 0, 10, 10)) is True

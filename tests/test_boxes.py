"""Tests for detection.boxes."""

from block_detected.detection.boxes import extract_boxes


class _FakeTensor:
    def __init__(self, values):
        self._values = values

    def tolist(self):
        return self._values


class _FakeBox:
    def __init__(self, xyxy):
        self.xyxy = [_FakeTensor(xyxy)]


class _FakeBoxes:
    def __init__(self, items):
        self._items = items

    def __iter__(self):
        return iter(self._items)


class _FakeResult:
    def __init__(self, boxes):
        self.boxes = boxes


def test_extract_boxes_empty():
    assert extract_boxes(_FakeResult(None)) == []


def test_extract_boxes_one():
    result = _FakeResult(_FakeBoxes([_FakeBox([1.2, 3.4, 5.6, 7.8])]))
    assert extract_boxes(result) == [(1, 3, 5, 7)]

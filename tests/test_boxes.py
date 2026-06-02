"""Tests for detection parse helpers."""

from block_detected.detection.boxes import extract_boxes, parse_yolo_result


class _FakeTensor:
    def __init__(self, values):
        self._values = values

    def tolist(self):
        return self._values

    def item(self):
        return self._values[0] if isinstance(self._values, list) else self._values


class _FakeBox:
    def __init__(self, xyxy, cls_id=0, conf=0.9):
        self.xyxy = [_FakeTensor(xyxy)]
        self.cls = [_FakeTensor([cls_id])]
        self.conf = [_FakeTensor([conf])]


class _FakeBoxes:
    def __init__(self, items):
        self._items = items

    def __iter__(self):
        return iter(self._items)


class _FakeResult:
    def __init__(self, boxes):
        self.boxes = boxes
        self.names = {0: "block"}


def test_parse_yolo_result_empty():
    result = parse_yolo_result(_FakeResult(None))
    assert result.detections == []


def test_parse_yolo_result_detection_fields():
    raw = _FakeResult(_FakeBoxes([_FakeBox([1.2, 3.4, 5.6, 7.8], cls_id=2, conf=0.75)]))
    parsed = parse_yolo_result(raw)
    assert len(parsed.detections) == 1
    det = parsed.detections[0]
    assert det.box == (1, 3, 5, 7)
    assert det.class_id == 2
    assert det.class_name == "2"
    assert det.confidence == 0.75


def test_extract_boxes_one():
    result = _FakeResult(_FakeBoxes([_FakeBox([1.2, 3.4, 5.6, 7.8])]))
    assert extract_boxes(result) == [(1, 3, 5, 7)]

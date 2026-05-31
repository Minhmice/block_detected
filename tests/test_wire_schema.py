"""Golden wire-format JSON contract tests (Phase 9)."""

from __future__ import annotations

import json
from pathlib import Path

FIXTURE_PATH = Path(__file__).parent / "fixtures" / "wire" / "detection_success.json"


def _load_fixture() -> dict:
    with FIXTURE_PATH.open(encoding="utf-8") as fh:
        return json.load(fh)


def test_golden_detection_json() -> None:
    data = _load_fixture()
    assert data["type"] == "telemetry"
    assert "fps" in data
    assert "latencyMs" in data
    assert "valid" in data
    assert "rejectReason" in data
    assert "classificationScores" in data
    detection = data["detection"]
    assert detection["blockId"] == 1
    assert "confidence" in detection
    assert "centerPx" in detection
    assert "cornersPx" in detection
    assert "angleDeg" in detection
    assert "pickupPoseMm" in detection


def test_corners_named_tl_tr_br_bl() -> None:
    corners = _load_fixture()["detection"]["cornersPx"]
    for key in ("tl", "tr", "br", "bl"):
        assert key in corners
        assert isinstance(corners[key]["x"], (int, float))
        assert isinstance(corners[key]["y"], (int, float))


def test_pickup_pose_mm_aliases() -> None:
    pose = _load_fixture()["detection"]["pickupPoseMm"]
    assert "xMm" in pose
    assert "yMm" in pose
    assert "thetaDeg" in pose
    assert "x_mm" not in pose

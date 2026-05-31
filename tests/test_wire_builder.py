"""Wire builder unit tests."""

from __future__ import annotations

import json
from pathlib import Path

from block_detected.detection_contract import SAMPLE_SUCCESS_BLOCK_1

from app.services.wire_builder import build_telemetry_from_contract

FIXTURE_PATH = Path(__file__).parent / "fixtures" / "wire" / "detection_success.json"


def test_builder_matches_golden_structure() -> None:
    golden = json.loads(FIXTURE_PATH.read_text(encoding="utf-8"))
    telemetry = build_telemetry_from_contract(
        SAMPLE_SUCCESS_BLOCK_1, fps=28.4, latency_ms=14.2
    )
    payload = telemetry.model_dump(by_alias=True)
    assert payload["type"] == golden["type"]
    assert "fps" in payload
    assert "latencyMs" in payload
    assert "detection" in payload
    det = payload["detection"]
    assert "blockId" in det
    assert "cornersPx" in det
    assert set(det["cornersPx"].keys()) == {"tl", "tr", "br", "bl"}
    assert "pickupPoseMm" in det or det.get("pickupPoseMm") is None
    assert "classificationScores" in payload

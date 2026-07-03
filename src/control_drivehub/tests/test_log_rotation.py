import time
from datetime import datetime, timezone
from pathlib import Path

from pi_monitor.core.schema import RobotState, TelemetryFrame
from pi_monitor.logging.jsonl import JsonlWriter


def test_jsonl_rotation_by_day(tmp_path: Path):
    writer = JsonlWriter(str(tmp_path))
    day1 = datetime(2026, 7, 3, 12, 0, 0, tzinfo=timezone.utc)
    day2 = datetime(2026, 7, 4, 12, 0, 0, tzinfo=timezone.utc)

    writer._ensure_day(day1.strftime("%Y-%m-%d"))
    writer.write(TelemetryFrame(seq=1, robot_state=RobotState.INIT))
    time.sleep(0.05)

    writer._ensure_day(day2.strftime("%Y-%m-%d"))
    writer.write(TelemetryFrame(seq=2, robot_state=RobotState.RUNNING))
    time.sleep(0.05)
    writer.close()

    assert (tmp_path / "telemetry-2026-07-03.jsonl").exists()
    assert (tmp_path / "telemetry-2026-07-04.jsonl").exists()

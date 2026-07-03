import time

from pi_monitor.core.schema import RobotState, TelemetryFrame
from pi_monitor.core.state import TelemetryState


def test_stale_when_no_packets():
    state = TelemetryState(stale_timeout_sec=1.0)
    assert state.is_stale() is True


def test_not_stale_after_ingest():
    state = TelemetryState(stale_timeout_sec=1.0)

    async def run():
        await state.ingest(
            TelemetryFrame(seq=1, ts_hub_ms=int(time.time() * 1000), robot_state=RobotState.RUNNING).model_dump(
                mode="json"
            )
        )
        assert state.is_stale() is False

    import asyncio

    asyncio.run(run())


def test_stale_after_timeout():
    state = TelemetryState(stale_timeout_sec=0.05)
    state.last_received_at_ms = int(time.time() * 1000) - 100
    assert state.is_stale() is True

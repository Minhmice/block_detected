"""Dashboard WebSocket fan-out."""

from __future__ import annotations

from typing import TYPE_CHECKING

from fastapi import WebSocket, WebSocketDisconnect

if TYPE_CHECKING:
    from pi_monitor.core.state import TelemetryState


async def dashboard_ws_endpoint(websocket: WebSocket, state: TelemetryState) -> None:
    await websocket.accept()
    state.dashboard_clients.add(websocket)
    try:
        await websocket.send_text(state.dashboard_envelope().model_dump_json())
        while True:
            await websocket.receive_text()
    except WebSocketDisconnect:
        pass
    finally:
        state.dashboard_clients.discard(websocket)

"""Control Hub WebSocket ingest."""

from __future__ import annotations

import json
from typing import TYPE_CHECKING

from fastapi import WebSocket, WebSocketDisconnect

if TYPE_CHECKING:
    from pi_monitor.core.state import TelemetryState


async def hub_ws_endpoint(websocket: WebSocket, state: TelemetryState, jsonl_writer, csv_writer) -> None:
    await websocket.accept()
    state.hub_connected = True
    state.hub_socket = websocket
    try:
        while True:
            raw = await websocket.receive_text()
            payload = json.loads(raw)
            frame = await state.ingest(payload)
            jsonl_writer.write(frame)
            csv_writer.write(frame)
            await state.broadcast_dashboard()
    except WebSocketDisconnect:
        pass
    finally:
        state.hub_connected = False
        if state.hub_socket is websocket:
            state.hub_socket = None

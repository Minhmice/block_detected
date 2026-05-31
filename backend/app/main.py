"""FastAPI application entrypoint.

Run from repo root:
  cd backend && pip install -r requirements.txt && pip install -e ..
  uvicorn app.main:app --reload --host 127.0.0.1 --port 8000 --workers 1
"""

from __future__ import annotations

import logging
import os
from contextlib import asynccontextmanager

from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware

from app.routes.calibration import router as calibration_router
from app.routes.camera import router as camera_router
from app.routes.dataset import router as dataset_router
from app.routes.detection import router as detection_router
from app.routes.eim import router as eim_router
from app.routes.health import router as health_router
from app.routes.stream import router as stream_router
from app.services.detection_loop import DetectionLoopService
from app.services.eim_model import is_vision_mock_mode, validate_eim_model
from app.services.frame_source_factory import is_mock_mode
from app.ws.manager import ConnectionManager

_log = logging.getLogger("block_detected")


@asynccontextmanager
async def lifespan(app: FastAPI):
    ws_manager = ConnectionManager()
    detection_loop = DetectionLoopService(ws_manager)
    app.state.ws_manager = ws_manager
    app.state.detection_loop = detection_loop
    if not is_vision_mock_mode():
        eim = validate_eim_model()
        if eim.error:
            _log.warning("EIM model check: %s", eim.error)
    if is_mock_mode():
        await detection_loop.start()
    yield
    await detection_loop.stop()


app = FastAPI(title="block_detected console", lifespan=lifespan)

_origins = os.getenv("CORS_ORIGINS", "http://localhost:3000").split(",")
app.add_middleware(
    CORSMiddleware,
    allow_origins=[o.strip() for o in _origins if o.strip()],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(health_router)
app.include_router(stream_router)
app.include_router(detection_router)
app.include_router(camera_router)
app.include_router(eim_router)
app.include_router(calibration_router)
app.include_router(dataset_router)


@app.websocket("/ws/detection")
async def ws_detection(websocket: WebSocket) -> None:
    manager: ConnectionManager = websocket.app.state.ws_manager
    await manager.connect(websocket)
    try:
        while True:
            await websocket.receive_text()
    except WebSocketDisconnect:
        manager.disconnect(websocket)

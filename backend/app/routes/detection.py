"""Detection control routes."""

from __future__ import annotations

from fastapi import APIRouter, Request

from app.schemas.wire import DetectionParamsWire

router = APIRouter(prefix="/api/detection", tags=["detection"])


@router.post("/start")
async def start_detection(request: Request) -> dict:
    await request.app.state.detection_loop.start()
    return {"started": True}


@router.post("/stop")
async def stop_detection(request: Request) -> dict:
    await request.app.state.detection_loop.stop()
    return {"started": False}


@router.post("/params")
async def update_params(body: DetectionParamsWire, request: Request) -> dict:
    request.app.state.detection_loop.apply_params(body)
    return {"ok": True}

"""Camera device listing and runtime configuration routes."""

from __future__ import annotations

import asyncio
import sys

from fastapi import APIRouter, Request

from app.schemas.wire import CameraConfigUpdateWire, CameraConfigWire, CameraDeviceWire
from app.services.camera_runtime import camera_runtime
from block_detected.camera import list_usb_camera_indices

router = APIRouter(prefix="/api/camera", tags=["camera"])

_LIVE_CV_BACKEND = "avfoundation" if sys.platform == "darwin" else "auto"
_PROBE_MAX_INDEX = 2 if sys.platform == "darwin" else 10


@router.get("/devices")
async def list_devices() -> dict:
    indices = await asyncio.to_thread(
        list_usb_camera_indices, _PROBE_MAX_INDEX, _LIVE_CV_BACKEND
    )
    devices = [
        CameraDeviceWire(index=i, label=f"Camera {i}").model_dump(by_alias=True)
        for i in indices
    ]
    return {"devices": devices}


@router.get("/config", response_model=CameraConfigWire)
async def get_config() -> CameraConfigWire:
    indices = await asyncio.to_thread(
        list_usb_camera_indices, _PROBE_MAX_INDEX, _LIVE_CV_BACKEND
    )
    return CameraConfigWire(
        mock_camera=camera_runtime.is_mock(),
        camera_index=camera_runtime.get_camera_index(),
        available_indices=indices,
    )


@router.post("/config", response_model=CameraConfigWire)
async def update_config(
    body: CameraConfigUpdateWire, request: Request
) -> CameraConfigWire:
    loop = request.app.state.detection_loop
    if loop.running:
        await loop.stop()

    if body.mock_camera is not None:
        camera_runtime.set_mock(body.mock_camera)
    if body.camera_index is not None:
        camera_runtime.set_camera_index(body.camera_index)

    indices = await asyncio.to_thread(
        list_usb_camera_indices, _PROBE_MAX_INDEX, _LIVE_CV_BACKEND
    )

    # Auto-start capture so MJPEG /video/stream has frames immediately
    await loop.start()

    return CameraConfigWire(
        mock_camera=camera_runtime.is_mock(),
        camera_index=camera_runtime.get_camera_index(),
        available_indices=indices,
    )

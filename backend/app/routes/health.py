"""Health check route."""

from __future__ import annotations

from fastapi import APIRouter, Request

from app.schemas.wire import SystemStatusWire
from app.services.eim_model import (
    get_selected_model_entry,
    is_vision_mock_mode,
    resolve_eim_path,
    validate_eim_model,
)
from app.services.frame_source_factory import is_mock_mode, preview_camera_backend
from app.services.camera_runtime import camera_runtime

router = APIRouter(tags=["health"])


@router.get("/health", response_model=SystemStatusWire)
async def health(request: Request) -> SystemStatusWire:
    loop = getattr(request.app.state, "detection_loop", None)
    running = loop.running if loop else False
    eim = validate_eim_model()
    vision_mock = is_vision_mock_mode()
    ei_loaded = eim.executable and not vision_mock
    selected = get_selected_model_entry()
    return SystemStatusWire(
        status="ok",
        mock_camera=is_mock_mode(),
        detection_running=running,
        camera_backend=preview_camera_backend(),
        camera_index=camera_runtime.get_camera_index(),
        vision_mock_mode=vision_mock,
        ei_model_path=str(resolve_eim_path()),
        ei_model_loaded=ei_loaded,
        ei_model_executable=eim.executable,
        ei_model_error=eim.error,
        ei_model_id=selected.id if selected else "",
        ei_model_label=selected.label if selected else "",
    )

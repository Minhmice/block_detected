"""Engine control REST endpoints."""

from __future__ import annotations

import logging

from block_detected.runtime.api.deps import get_engine_service
from block_detected.runtime.api.schemas import ControlResponse, EngineStateResponse
from block_detected.runtime.api.service import EngineService

logger = logging.getLogger(__name__)

router = None


def _get_router():
    from fastapi import APIRouter, Depends
    from fastapi.responses import JSONResponse

    api = APIRouter(tags=["control"])

    @api.post("/api/start", response_model=ControlResponse)
    def start_engine(service: EngineService = Depends(get_engine_service)) -> ControlResponse:
        if service.is_running:
            logger.info("POST /api/start — already running")
            return ControlResponse(ok=True, message="already running")
        ok, err = service.start()
        logger.info("POST /api/start — ok=%s", ok)
        return ControlResponse(ok=ok, message=err)

    @api.post("/api/stop", response_model=ControlResponse)
    def stop_engine(service: EngineService = Depends(get_engine_service)) -> ControlResponse:
        service.stop()
        logger.info("POST /api/stop")
        return ControlResponse(ok=True)

    @api.post("/api/camera/next", response_model=ControlResponse)
    def next_camera(service: EngineService = Depends(get_engine_service)):
        if not service.is_running:
            body = ControlResponse(ok=False, message="engine not running")
            return JSONResponse(status_code=409, content=body.model_dump())
        switched = service.switch_camera()
        logger.info("POST /api/camera/next — switched=%s", switched)
        if not switched:
            return ControlResponse(ok=False, message="no other camera available")
        return ControlResponse(ok=True)

    @api.post("/api/model/next", response_model=ControlResponse)
    def next_model(service: EngineService = Depends(get_engine_service)):
        if not service.is_running:
            body = ControlResponse(ok=False, message="engine not running")
            return JSONResponse(status_code=409, content=body.model_dump())
        service.switch_model()
        logger.info("POST /api/model/next")
        return ControlResponse(ok=True)

    @api.get("/api/state", response_model=EngineStateResponse)
    def engine_state(service: EngineService = Depends(get_engine_service)) -> EngineStateResponse:
        status = service.get_status()
        return EngineStateResponse(
            running=service.is_running,
            model_name=status.model_name if status else None,
            camera_index=status.camera_index if status else None,
            error=service.last_error,
        )

    return api


router = _get_router()

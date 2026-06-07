"""Telemetry and log tail endpoints."""

from __future__ import annotations

from block_detected.runtime.api.deps import get_engine_service
from block_detected.runtime.api.schemas import LogsResponse, TelemetryResponse, telemetry_from_status
from block_detected.runtime.api.service import EngineService
from block_detected.runtime.logging_setup import get_log_lines

router = None


def _get_router():
    from fastapi import APIRouter, Depends, Query

    api = APIRouter(tags=["telemetry"])

    @api.get("/api/telemetry", response_model=TelemetryResponse)
    def telemetry(service: EngineService = Depends(get_engine_service)) -> TelemetryResponse:
        return telemetry_from_status(service.get_status(), running=service.is_running)

    @api.get("/api/logs", response_model=LogsResponse)
    def logs(limit: int = Query(default=50, ge=1, le=500)) -> LogsResponse:
        lines = get_log_lines()
        tail = lines[-limit:]
        return LogsResponse(lines=tail, count=len(tail))

    return api


router = _get_router()

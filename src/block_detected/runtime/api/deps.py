"""FastAPI dependencies for runtime API routes."""

from __future__ import annotations

from starlette.requests import Request

from block_detected.runtime.api.service import EngineService


def get_engine_service(request: Request) -> EngineService:
    return request.app.state.engine_service

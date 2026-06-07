"""FastAPI dependencies for runtime API routes."""

from __future__ import annotations

from typing import TYPE_CHECKING

from block_detected.runtime.api.service import EngineService

if TYPE_CHECKING:
    from fastapi import Request


def get_engine_service(request: Request) -> EngineService:
    return request.app.state.engine_service

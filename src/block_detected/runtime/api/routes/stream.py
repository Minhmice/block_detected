"""MJPEG frame streaming endpoint."""

from __future__ import annotations

import asyncio
import logging
from collections.abc import AsyncIterator

from block_detected.runtime.api.deps import get_engine_service
from block_detected.runtime.api.service import EngineService

logger = logging.getLogger(__name__)


async def mjpeg_frames(service: EngineService) -> AsyncIterator[bytes]:
    try:
        while True:
            jpeg = service.get_latest_jpeg()
            if jpeg:
                header = (
                    b"--frame\r\n"
                    b"Content-Type: image/jpeg\r\n"
                    + f"Content-Length: {len(jpeg)}\r\n\r\n".encode()
                    + jpeg
                    + b"\r\n"
                )
                yield header
            await asyncio.sleep(0.033)
    except asyncio.CancelledError:
        logger.debug("MJPEG stream client disconnected")
        raise


def _get_router():
    from fastapi import APIRouter, Depends
    from starlette.responses import StreamingResponse

    api = APIRouter(tags=["stream"])

    @api.get("/stream")
    async def stream(service: EngineService = Depends(get_engine_service)):
        return StreamingResponse(
            mjpeg_frames(service),
            media_type="multipart/x-mixed-replace; boundary=frame",
        )

    return api


router = _get_router()

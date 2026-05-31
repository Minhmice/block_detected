"""MJPEG video stream."""

from __future__ import annotations

import asyncio

from fastapi import APIRouter, Request
from fastapi.responses import StreamingResponse

router = APIRouter(tags=["stream"])


async def _mjpeg_generator(request: Request):
    loop = request.app.state.detection_loop
    boundary = b"frame"
    while True:
        if await request.is_disconnected():
            break
        jpeg = loop.latest_jpeg()
        if jpeg:
            yield (
                b"--" + boundary + b"\r\n"
                b"Content-Type: image/jpeg\r\n\r\n" + jpeg + b"\r\n"
            )
        await asyncio.sleep(1.0 / 30.0)


@router.get("/video/stream")
async def video_stream(request: Request) -> StreamingResponse:
    return StreamingResponse(
        _mjpeg_generator(request),
        media_type="multipart/x-mixed-replace; boundary=frame",
        headers={
            "Cache-Control": "no-cache, no-store, must-revalidate",
            "Pragma": "no-cache",
            "X-Accel-Buffering": "no",
        },
    )

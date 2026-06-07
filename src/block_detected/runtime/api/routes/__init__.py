"""HTTP route modules for the web API."""

from block_detected.runtime.api.routes.control import router as control_router
from block_detected.runtime.api.routes.stream import router as stream_router

__all__ = ["control_router", "stream_router"]

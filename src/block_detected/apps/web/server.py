"""FastAPI app factory and uvicorn entry for the Stitch web console."""

from __future__ import annotations

import argparse
import logging
from contextlib import asynccontextmanager
from typing import TYPE_CHECKING

from block_detected.runtime.api.service import EngineService
from block_detected.runtime.config_schema import AppConfig
from block_detected.runtime.config_store import load_config
from block_detected.runtime.logging_setup import setup_logging

if TYPE_CHECKING:
    from fastapi import FastAPI, Request

logger = logging.getLogger(__name__)


def get_engine_service(request: Request) -> EngineService:
    return request.app.state.engine_service


def create_app(*, config: AppConfig | None = None):
    from fastapi import FastAPI
    from fastapi.middleware.cors import CORSMiddleware

    app_config = config if config is not None else load_config()
    engine_service = EngineService(app_config)

    @asynccontextmanager
    async def lifespan(app: FastAPI):
        yield
        engine_service.stop()

    app = FastAPI(title="Block Detected Web", lifespan=lifespan)
    app.state.engine_service = engine_service

    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_methods=["*"],
        allow_headers=["*"],
    )

    @app.get("/health")
    def health() -> dict[str, str]:
        return {"status": "ok"}

    return app


def main() -> None:
    parser = argparse.ArgumentParser(description="Block Detected web API server")
    parser.add_argument("--host", default="127.0.0.1", help="Bind host (default: 127.0.0.1)")
    parser.add_argument("--port", type=int, default=8765, help="Bind port (default: 8765)")
    args = parser.parse_args()

    try:
        import uvicorn
    except ImportError:
        print('Web server requires optional deps: pip install -e ".[web]"')
        raise SystemExit(1) from None

    setup_logging()
    uvicorn.run(create_app(), host=args.host, port=args.port)

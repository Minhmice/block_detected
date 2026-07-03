"""FastAPI application factory."""

from __future__ import annotations

import asyncio
from contextlib import asynccontextmanager

from fastapi import FastAPI, WebSocket
from fastapi.middleware.cors import CORSMiddleware

from pi_monitor.api.routes import attach_routes, router
from pi_monitor.broadcast.dashboard_ws import dashboard_ws_endpoint
from pi_monitor.core.config import AppConfig
from pi_monitor.core.state import TelemetryState
from pi_monitor.ingest.hub_ws import hub_ws_endpoint
from pi_monitor.ingest.simulator import run_simulator
from pi_monitor.logging.csv import CsvWriter
from pi_monitor.logging.jsonl import JsonlWriter


def create_app(config: AppConfig, *, simulate: bool = False) -> FastAPI:
    state = TelemetryState(stale_timeout_sec=config.telemetry.stale_timeout_sec)
    jsonl_writer = JsonlWriter(config.logging.dir)
    csv_writer = CsvWriter(config.logging.dir)
    sim_task: asyncio.Task | None = None

    @asynccontextmanager
    async def lifespan(app: FastAPI):
        nonlocal sim_task
        if simulate or config.simulator.enabled:
            sim_task = asyncio.create_task(run_simulator(config, state, jsonl_writer, csv_writer))
        yield
        if sim_task is not None:
            sim_task.cancel()
            try:
                await sim_task
            except asyncio.CancelledError:
                pass
        jsonl_writer.close()
        csv_writer.close()

    app = FastAPI(title="PiMonitor", version="1.0.0", lifespan=lifespan)
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    attach_routes(router, config, state)
    app.include_router(router)

    @app.websocket("/ws/hub")
    async def ws_hub(websocket: WebSocket):
        await hub_ws_endpoint(websocket, state, jsonl_writer, csv_writer)

    @app.websocket("/ws/dashboard")
    async def ws_dashboard(websocket: WebSocket):
        await dashboard_ws_endpoint(websocket, state)

    app.state.config = config
    app.state.telemetry_state = state
    return app


def build_app(config_path: str, *, simulate: bool = False) -> FastAPI:
    from pi_monitor.core.config import load_config

    config = load_config(config_path)
    return create_app(config, simulate=simulate)

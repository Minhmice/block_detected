"""REST routes."""

from __future__ import annotations

from pathlib import Path

from fastapi import APIRouter, Header, HTTPException

from pi_monitor.core.commands import validate_command
from pi_monitor.core.config import AppConfig
from pi_monitor.core.schema import CommandRequest, StatusResponse
from pi_monitor.core.state import TelemetryState

router = APIRouter()


def attach_routes(app_router: APIRouter, config: AppConfig, state: TelemetryState) -> None:
    @app_router.get("/api/status", response_model=StatusResponse)
    async def get_status() -> StatusResponse:
        data = state.status_dict()
        return StatusResponse(**data)

    @app_router.get("/api/config")
    async def get_config() -> dict:
        return {
            "telemetry": {
                "rate_hz": config.telemetry.rate_hz,
                "stale_timeout_sec": config.telemetry.stale_timeout_sec,
            },
            "commands": {
                "enabled": config.commands.enabled,
                "whitelist": config.commands.whitelist,
            },
            "hardware_names": {
                "motors": config.hardware_names.motors,
                "servos": config.hardware_names.servos,
                "imu": config.hardware_names.imu,
            },
        }

    @app_router.get("/api/history")
    async def get_history(lines: int = 50) -> dict:
        log_dir = Path(config.logging.dir)
        if not log_dir.exists():
            return {"lines": []}
        files = sorted(log_dir.glob("telemetry-*.jsonl"))
        if not files:
            return {"lines": []}
        content = files[-1].read_text(encoding="utf-8").splitlines()
        tail = content[-lines:]
        return {"file": str(files[-1]), "lines": tail}

    @app_router.post("/api/command")
    async def post_command(
        request: CommandRequest,
        x_command_token: str | None = Header(default=None),
    ) -> dict:
        result = validate_command(config.commands, request, x_command_token)
        if not result.ok:
            raise HTTPException(status_code=403, detail=result.reason)
        payload = request.model_dump(mode="json")
        sent = await state.send_command_to_hub(payload)
        if not sent:
            raise HTTPException(status_code=503, detail="hub not connected")
        return {"ok": True, "type": request.type}

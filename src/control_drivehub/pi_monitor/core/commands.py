"""Command whitelist validation."""

from __future__ import annotations

from dataclasses import dataclass

from pi_monitor.core.config import CommandsConfig
from pi_monitor.core.schema import CommandRequest


@dataclass
class CommandValidation:
    ok: bool
    reason: str = ""


def validate_command(config: CommandsConfig, request: CommandRequest, header_token: str | None = None) -> CommandValidation:
    if not config.enabled:
        return CommandValidation(False, "commands disabled")

    token = header_token or request.token
    if token != config.token:
        return CommandValidation(False, "invalid token")

    if request.type not in config.whitelist:
        return CommandValidation(False, f"command '{request.type}' not whitelisted")

    return CommandValidation(True)

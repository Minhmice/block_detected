"""YAML configuration loader."""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import yaml


@dataclass
class HubConfig:
    listen_host: str = "0.0.0.0"
    ws_port: int = 8765


@dataclass
class ApiConfig:
    host: str = "0.0.0.0"
    port: int = 8080


@dataclass
class TelemetryConfig:
    rate_hz: int = 20
    stale_timeout_sec: float = 1.0


@dataclass
class LoggingConfig:
    dir: str = "./logs"
    rotate: str = "daily"


@dataclass
class CommandsConfig:
    enabled: bool = False
    token: str = "change-me"
    whitelist: list[str] = field(default_factory=lambda: ["emergency_stop"])


@dataclass
class SimulatorConfig:
    enabled: bool = False


@dataclass
class HardwareNamesConfig:
    motors: list[str] = field(default_factory=list)
    servos: list[str] = field(default_factory=list)
    imu: str = "imu"


@dataclass
class AppConfig:
    hub: HubConfig = field(default_factory=HubConfig)
    api: ApiConfig = field(default_factory=ApiConfig)
    telemetry: TelemetryConfig = field(default_factory=TelemetryConfig)
    logging: LoggingConfig = field(default_factory=LoggingConfig)
    commands: CommandsConfig = field(default_factory=CommandsConfig)
    simulator: SimulatorConfig = field(default_factory=SimulatorConfig)
    hardware_names: HardwareNamesConfig = field(default_factory=HardwareNamesConfig)


def _section(data: dict[str, Any], key: str) -> dict[str, Any]:
    value = data.get(key, {})
    return value if isinstance(value, dict) else {}


def load_config(path: str | Path) -> AppConfig:
    raw = yaml.safe_load(Path(path).read_text(encoding="utf-8")) or {}
    hub = _section(raw, "hub")
    api = _section(raw, "api")
    telemetry = _section(raw, "telemetry")
    logging_cfg = _section(raw, "logging")
    commands = _section(raw, "commands")
    simulator = _section(raw, "simulator")
    hardware = _section(raw, "hardware_names")

    return AppConfig(
        hub=HubConfig(
            listen_host=str(hub.get("listen_host", "0.0.0.0")),
            ws_port=int(hub.get("ws_port", 8765)),
        ),
        api=ApiConfig(
            host=str(api.get("host", "0.0.0.0")),
            port=int(api.get("port", 8080)),
        ),
        telemetry=TelemetryConfig(
            rate_hz=int(telemetry.get("rate_hz", 20)),
            stale_timeout_sec=float(telemetry.get("stale_timeout_sec", 1.0)),
        ),
        logging=LoggingConfig(
            dir=str(logging_cfg.get("dir", "./logs")),
            rotate=str(logging_cfg.get("rotate", "daily")),
        ),
        commands=CommandsConfig(
            enabled=bool(commands.get("enabled", False)),
            token=str(commands.get("token", "change-me")),
            whitelist=list(commands.get("whitelist", ["emergency_stop"])),
        ),
        simulator=SimulatorConfig(enabled=bool(simulator.get("enabled", False))),
        hardware_names=HardwareNamesConfig(
            motors=list(hardware.get("motors", [])),
            servos=list(hardware.get("servos", [])),
            imu=str(hardware.get("imu", "imu")),
        ),
    )

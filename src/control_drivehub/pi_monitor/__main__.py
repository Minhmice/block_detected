"""PiMonitor CLI entry point."""

from __future__ import annotations

import argparse
import sys
import threading
from pathlib import Path

import uvicorn

DEFAULT_CONFIG = Path(__file__).resolve().parent / "config.example.yaml"


def _run_server(app_import: str, host: str, port: int) -> None:
    uvicorn.run(app_import, host=host, port=port, factory=False, log_level="info")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="PiMonitor — REV Control Hub telemetry server")
    sub = parser.add_subparsers(dest="command", required=True)

    serve = sub.add_parser("serve", help="Run API + WebSocket servers")
    serve.add_argument("--config", default=str(DEFAULT_CONFIG), help="Path to YAML config")
    serve.add_argument("--simulate", action="store_true", help="Enable built-in telemetry simulator")

    sim = sub.add_parser("simulate", help="Run server with simulator enabled")
    sim.add_argument("--config", default=str(DEFAULT_CONFIG), help="Path to YAML config")

    args = parser.parse_args(argv)
    config_path = args.config

    if args.command == "simulate":
        simulate = True
    else:
        simulate = bool(getattr(args, "simulate", False))

    # Set env for factory app
    import os

    os.environ["PIMONITOR_CONFIG"] = config_path
    os.environ["PIMONITOR_SIMULATE"] = "1" if simulate else "0"

    from pi_monitor.core.config import load_config

    config = load_config(config_path)

    def factory():
        from pi_monitor.api.app import build_app

        return build_app(config_path, simulate=simulate)

    threads: list[threading.Thread] = []
    if config.hub.ws_port != config.api.port:
        hub_thread = threading.Thread(
            target=lambda: uvicorn.run(factory, host=config.hub.listen_host, port=config.hub.ws_port, factory=True),
            daemon=True,
            name="hub-ws",
        )
        hub_thread.start()
        threads.append(hub_thread)

    uvicorn.run(
        factory,
        host=config.api.host,
        port=config.api.port,
        factory=True,
        log_level="info",
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())

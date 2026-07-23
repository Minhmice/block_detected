"""UART sender — gửi detection class IDs + robot commands sang ESP32.

Detection protocol: 0xAA | count (1B) | [cls_id (1B)] * N | checksum | 0x55
Robot cmd protocol:  0xBB | CMD (1B) | SPEED_L (1B) | SPEED_R (1B) | checksum | 0xCC
"""

from __future__ import annotations

import logging
import threading
import time
from dataclasses import dataclass
from typing import Any

from block_detected.core.domain import Detection
from block_detected.runtime.robo_nav import RobotCommand

logger = logging.getLogger(__name__)

# Detection frame markers
FRAME_START = 0xAA
FRAME_END = 0x55
MAX_DETS = 10

# Robot command markers
ROBO_START = 0xBB
ROBO_END = 0xCC


@dataclass
class UartSenderConfig:
    port: str = "/dev/ttyAMA0"
    baud: int = 115200
    rate_hz: float = 10.0


class UartSender:
    def __init__(self, config: UartSenderConfig | None = None) -> None:
        self.config = config or UartSenderConfig()
        self._ser: Any = None
        self._detections: list[Detection] = []
        self._robot_cmd: RobotCommand | None = None
        self._lock = threading.Lock()
        self._running = False
        self._thread: threading.Thread | None = None

    def start(self) -> bool:
        try:
            import serial
            self._ser = serial.Serial(
                port=self.config.port,
                baudrate=self.config.baud,
                timeout=0.01,
            )
        except Exception as exc:
            logger.warning("UART not available (%s). Running without it.", exc)
            return False

        self._running = True
        self._thread = threading.Thread(target=self._send_loop, daemon=True)
        self._thread.start()
        logger.info("UART sender started on %s @ %d", self.config.port, self.config.baud)
        return True

    # ------------------------------------------------------------------
    # Detection push (existing)
    # ------------------------------------------------------------------

    def push(self, detections: list[Detection]) -> None:
        with self._lock:
            self._detections = detections

    # ------------------------------------------------------------------
    # Robot command push (new)
    # ------------------------------------------------------------------

    def push_robot_cmd(self, cmd: RobotCommand) -> None:
        """Queue a robot movement command. Overwrites previous unsent cmd."""
        with self._lock:
            self._robot_cmd = cmd

    # ------------------------------------------------------------------
    # Send loop
    # ------------------------------------------------------------------

    def _send_loop(self) -> None:
        while self._running:
            with self._lock:
                dets = list(self._detections)
                rcmd = self._robot_cmd
                self._robot_cmd = None  # consume
            self._send_detection(dets)
            if rcmd is not None:
                self._send_robot_cmd(rcmd)
            time.sleep(1.0 / self.config.rate_hz)

    # ------------------------------------------------------------------
    # Detection protocol: 0xAA | count | [cls_id]*N | cksum | 0x55
    # ------------------------------------------------------------------

    def _send_detection(self, detections: list[Detection]) -> None:
        if self._ser is None:
            return

        count = min(len(detections), MAX_DETS)
        payload = bytearray()
        payload.append(FRAME_START)
        payload.append(count)
        for d in detections[:count]:
            payload.append(d.class_id & 0xFF)
        checksum = sum(payload[1:]) & 0xFF
        payload.append(checksum)
        payload.append(FRAME_END)

        try:
            self._ser.write(payload)
        except Exception as exc:
            logger.debug("UART detection write error: %s", exc)

    # ------------------------------------------------------------------
    # Robot command protocol: 0xBB | CMD | SPD_L | SPD_R | cksum | 0xCC
    # ------------------------------------------------------------------

    def _send_robot_cmd(self, cmd: RobotCommand) -> None:
        if self._ser is None:
            return

        speed = min(255, max(0, cmd.speed))
        payload = bytearray()
        payload.append(ROBO_START)
        payload.append(cmd.command & 0xFF)
        payload.append(speed)
        payload.append(speed)  # same speed both sides (differential add if needed)
        checksum = sum(payload[1:4]) & 0xFF
        payload.append(checksum)
        payload.append(ROBO_END)

        try:
            self._ser.write(payload)
        except Exception as exc:
            logger.debug("UART robot cmd write error: %s", exc)

    def stop(self) -> None:
        self._running = False
        if self._ser is not None:
            try:
                self._ser.close()
            except Exception:
                pass
            self._ser = None


# Singleton — dễ tích hợp
_sender: UartSender | None = None


def get_sender() -> UartSender | None:
    global _sender
    return _sender


def init_sender(config: UartSenderConfig | None = None) -> UartSender | None:
    global _sender
    if _sender is None:
        _sender = UartSender(config)
        _sender.start()
    return _sender


def push_detections(detections: list[Detection]) -> None:
    s = get_sender()
    if s is not None:
        s.push(detections)


def push_robot_command(cmd: RobotCommand) -> None:
    """Send a robot movement command via UART."""
    s = get_sender()
    if s is not None:
        s.push_robot_cmd(cmd)

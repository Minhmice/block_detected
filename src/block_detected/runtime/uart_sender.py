"""UART sender — gửi detection class IDs sang ESP32.

Protocol: 0xAA | count (1B) | [cls_id (1B)] * N | checksum | 0x55
"""

from __future__ import annotations

import logging
import struct
import threading
import time
from dataclasses import dataclass, field

from block_detected.core.domain import Detection

logger = logging.getLogger(__name__)

FRAME_START = 0xAA
FRAME_END = 0x55
MAX_DETS = 10


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

    def push(self, detections: list[Detection]) -> None:
        with self._lock:
            self._detections = detections

    def _send_loop(self) -> None:
        while self._running:
            with self._lock:
                dets = self._detections
            self._send(dets)
            time.sleep(1.0 / self.config.rate_hz)

    def _send(self, detections: list[Detection]) -> None:
        if self._ser is None:
            return

        count = min(len(detections), MAX_DETS)
        if count == 0:
            return

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
            logger.debug("UART write error: %s", exc)

    def stop(self) -> None:
        self._running = False
        if self._ser is not None:
            try:
                self._ser.close()
            except Exception:
                pass
            self._ser = None


# Singleton cho dễ tích hợp
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

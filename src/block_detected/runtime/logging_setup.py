"""Central logging setup for CLI and future GUI log panel."""

import logging
import sys
import threading
from collections import deque
from dataclasses import dataclass, field
from typing import Deque


class LogBufferHandler(logging.Handler):
    """Ring buffer of recent log records for GUI consumption."""

    def __init__(self, capacity: int = 500) -> None:
        super().__init__()
        self._lock = threading.Lock()
        self._records: Deque[str] = deque(maxlen=capacity)

    def emit(self, record: logging.LogRecord) -> None:
        line = self.format(record)
        with self._lock:
            self._records.append(line)

    def snapshot_lines(self) -> list[str]:
        """Thread-safe copy of buffered log lines for UI display."""
        with self._lock:
            return list(self._records)


@dataclass
class LoggingContext:
    buffer_handler: LogBufferHandler = field(default_factory=LogBufferHandler)


_CONTEXT = LoggingContext()


def setup_logging(level: str = "INFO") -> LogBufferHandler:
    root = logging.getLogger()
    root.handlers.clear()
    root.setLevel(getattr(logging, level.upper(), logging.INFO))

    formatter = logging.Formatter("%(asctime)s [%(levelname)s] %(name)s: %(message)s")

    stream = logging.StreamHandler(sys.stdout)
    stream.setFormatter(formatter)
    root.addHandler(stream)

    _CONTEXT.buffer_handler.setFormatter(formatter)
    _CONTEXT.buffer_handler.setLevel(logging.DEBUG)
    root.addHandler(_CONTEXT.buffer_handler)

    logging.getLogger("ultralytics").setLevel(logging.WARNING)
    return _CONTEXT.buffer_handler


def get_log_buffer() -> LogBufferHandler:
    return _CONTEXT.buffer_handler


def get_log_lines() -> list[str]:
    """Return a thread-safe snapshot of recent log lines."""
    return _CONTEXT.buffer_handler.snapshot_lines()

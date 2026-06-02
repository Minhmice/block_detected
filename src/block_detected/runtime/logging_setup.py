"""Central logging setup for CLI and future GUI log panel."""

import logging
import sys
from collections import deque
from dataclasses import dataclass, field
from typing import Deque


class LogBufferHandler(logging.Handler):
    """Ring buffer of recent log records for GUI consumption."""

    def __init__(self, capacity: int = 500) -> None:
        super().__init__()
        self.records: Deque[str] = deque(maxlen=capacity)

    def emit(self, record: logging.LogRecord) -> None:
        self.records.append(self.format(record))


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

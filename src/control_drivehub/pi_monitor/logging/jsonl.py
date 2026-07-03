"""Daily-rotating JSONL telemetry writer."""

from __future__ import annotations

import json
import queue
import threading
import time
from datetime import datetime, timezone
from pathlib import Path

from pi_monitor.core.schema import TelemetryFrame


class JsonlWriter:
    def __init__(self, log_dir: str, max_queue: int = 256) -> None:
        self._log_dir = Path(log_dir)
        self._log_dir.mkdir(parents=True, exist_ok=True)
        self._queue: queue.Queue[TelemetryFrame | None] = queue.Queue(maxsize=max_queue)
        self._current_day: str | None = None
        self._handle = None
        self._stop = threading.Event()
        self._thread = threading.Thread(target=self._run, name="jsonl-writer", daemon=True)
        self._thread.start()

    def _path_for_day(self, day: str) -> Path:
        return self._log_dir / f"telemetry-{day}.jsonl"

    def _ensure_day(self, day: str) -> None:
        if self._current_day == day and self._handle is not None:
            return
        if self._handle is not None:
            self._handle.close()
        self._current_day = day
        self._handle = self._path_for_day(day).open("a", encoding="utf-8")

    def write(self, frame: TelemetryFrame) -> None:
        try:
            self._queue.put_nowait(frame)
        except queue.Full:
            try:
                self._queue.get_nowait()
            except queue.Empty:
                pass
            try:
                self._queue.put_nowait(frame)
            except queue.Full:
                pass

    def _run(self) -> None:
        while not self._stop.is_set():
            try:
                frame = self._queue.get(timeout=0.2)
            except queue.Empty:
                continue
            if frame is None:
                break
            day = datetime.now(timezone.utc).strftime("%Y-%m-%d")
            self._ensure_day(day)
            assert self._handle is not None
            self._handle.write(frame.model_dump_json() + "\n")
            self._handle.flush()

    def close(self) -> None:
        self._stop.set()
        try:
            self._queue.put_nowait(None)
        except queue.Full:
            pass
        self._thread.join(timeout=2)
        if self._handle is not None:
            self._handle.close()

    def current_path(self) -> Path | None:
        if self._current_day is None:
            return None
        return self._path_for_day(self._current_day)

    @staticmethod
    def day_key_from_ms(ms: int) -> str:
        return datetime.fromtimestamp(ms / 1000, tz=timezone.utc).strftime("%Y-%m-%d")

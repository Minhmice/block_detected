"""Daily-rotating CSV telemetry writer."""

from __future__ import annotations

import csv
import queue
import threading
from datetime import datetime, timezone
from pathlib import Path

from pi_monitor.core.schema import TelemetryFrame


CSV_HEADER = [
    "seq",
    "ts_hub_ms",
    "robot_state",
    "driver_hub_connected",
    "loop_time_ms",
    "battery_v",
    "latency_ms",
    "imu_yaw",
    "imu_pitch",
    "imu_roll",
    "gp1_lx",
    "gp1_ly",
    "gp2_lx",
    "gp2_ly",
]


class CsvWriter:
    def __init__(self, log_dir: str, max_queue: int = 256) -> None:
        self._log_dir = Path(log_dir)
        self._log_dir.mkdir(parents=True, exist_ok=True)
        self._queue: queue.Queue[TelemetryFrame | None] = queue.Queue(maxsize=max_queue)
        self._current_day: str | None = None
        self._handle = None
        self._writer: csv.DictWriter | None = None
        self._stop = threading.Event()
        self._thread = threading.Thread(target=self._run, name="csv-writer", daemon=True)
        self._thread.start()

    def _path_for_day(self, day: str) -> Path:
        return self._log_dir / f"telemetry-{day}.csv"

    def _ensure_day(self, day: str) -> None:
        if self._current_day == day and self._handle is not None:
            return
        if self._handle is not None:
            self._handle.close()
        self._current_day = day
        path = self._path_for_day(day)
        new_file = not path.exists()
        self._handle = path.open("a", encoding="utf-8", newline="")
        self._writer = csv.DictWriter(self._handle, fieldnames=CSV_HEADER)
        if new_file:
            self._writer.writeheader()

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

    def _row(self, frame: TelemetryFrame) -> dict[str, object]:
        return {
            "seq": frame.seq,
            "ts_hub_ms": frame.ts_hub_ms,
            "robot_state": frame.robot_state.value,
            "driver_hub_connected": frame.driver_hub_connected,
            "loop_time_ms": frame.loop_time_ms,
            "battery_v": frame.battery_v,
            "latency_ms": frame.latency_ms,
            "imu_yaw": frame.imu.yaw,
            "imu_pitch": frame.imu.pitch,
            "imu_roll": frame.imu.roll,
            "gp1_lx": frame.gamepad1.left_stick_x,
            "gp1_ly": frame.gamepad1.left_stick_y,
            "gp2_lx": frame.gamepad2.left_stick_x,
            "gp2_ly": frame.gamepad2.left_stick_y,
        }

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
            assert self._writer is not None
            self._writer.writerow(self._row(frame))
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

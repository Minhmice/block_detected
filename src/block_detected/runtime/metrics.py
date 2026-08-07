"""Runtime timing metrics (FPS and stage latencies)."""

from collections import deque
from dataclasses import dataclass, field
from time import perf_counter

from block_detected.core.domain import InferenceStats


@dataclass
class RuntimeMetrics:
    _frame_times: deque[float] = field(default_factory=lambda: deque(maxlen=30))
    last_stats: InferenceStats = field(default_factory=InferenceStats)

    def begin_frame(self) -> float:
        return perf_counter()

    def record(
        self,
        *,
        frame_start: float,
        read_end: float,
        infer_end: float,
        render_end: float,
        model_name: str,
        camera_index: int,
    ) -> InferenceStats:
        frame_read_ms = (read_end - frame_start) * 1000.0
        inference_ms = (infer_end - read_end) * 1000.0
        render_ms = (render_end - infer_end) * 1000.0
        total_s = render_end - frame_start
        if total_s > 0:
            self._frame_times.append(total_s)

        fps = 0.0
        if self._frame_times:
            avg = sum(self._frame_times) / len(self._frame_times)
            fps = 1.0 / avg if avg > 0 else 0.0

        self.last_stats = InferenceStats(
            fps=fps,
            frame_read_ms=frame_read_ms,
            inference_ms=inference_ms,
            render_ms=render_ms,
            model_name=model_name,
            camera_index=camera_index,
        )
        return self.last_stats

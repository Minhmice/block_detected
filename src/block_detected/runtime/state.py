"""Mutable runtime session state (hot-reload friendly fields)."""

from collections import deque
from dataclasses import dataclass, field

from block_detected.core.types import Box


@dataclass
class RuntimeState:
    confidence: float = 0.25
    overlay_enabled: bool = True
    eval_mode: bool = False
    camera_index: int = 0
    model_index: int = 0
    box_history: deque[list[Box]] = field(default_factory=deque)

    def reset_overlay_history(self, maxlen: int) -> None:
        self.box_history = deque(maxlen=maxlen)

    def set_overlay_maxlen(self, maxlen: int) -> None:
        history = list(self.box_history)
        self.box_history = deque(history[-maxlen:], maxlen=maxlen)

"""Mutable runtime session state (hot-reload friendly fields)."""

from dataclasses import dataclass


@dataclass
class RuntimeState:
    confidence: float = 0.25
    eval_mode: bool = False
    camera_index: int = 0
    model_index: int = 0

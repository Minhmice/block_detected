"""Runtime Edge Impulse model selection (UI-driven)."""

from __future__ import annotations

from dataclasses import dataclass, field


@dataclass
class EimRuntimeState:
    selected_id: str | None = field(default=None)

    def get_selected_id(self) -> str | None:
        return self.selected_id

    def set_selected_id(self, model_id: str) -> None:
        self.selected_id = model_id

    def reset_for_tests(self) -> None:
        self.selected_id = None


eim_runtime = EimRuntimeState()

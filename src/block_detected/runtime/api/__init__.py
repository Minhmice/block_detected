"""HTTP-facing runtime wrappers (no FastAPI imports here)."""

from block_detected.runtime.api.service import EngineService

__all__ = ["EngineService"]

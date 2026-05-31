"""Shared coercion helpers for detection parameter wire values."""

from __future__ import annotations


def coerce_odd_kernel(value: int, *, min_value: int = 1, max_value: int = 15) -> int:
    """Gaussian blur kernels must be odd positive integers."""
    coerced = max(min_value, min(max_value, int(value)))
    if coerced % 2 == 0:
        coerced = min(max_value, coerced + 1)
    return coerced

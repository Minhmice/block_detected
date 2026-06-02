"""Tests for runtime state."""

from block_detected.runtime.state import RuntimeState


def test_overlay_maxlen_resize():
    state = RuntimeState()
    state.reset_overlay_history(3)
    state.box_history.append([(0, 0, 1, 1)])
    state.box_history.append([(1, 1, 2, 2)])
    state.box_history.append([(2, 2, 3, 3)])
    state.box_history.append([(3, 3, 4, 4)])
    assert len(state.box_history) == 3
    state.set_overlay_maxlen(2)
    assert state.box_history.maxlen == 2
    assert len(state.box_history) <= 2

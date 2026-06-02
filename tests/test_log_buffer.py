"""Thread-safe log buffer snapshot API."""

import logging
import threading

from block_detected.runtime.logging_setup import LogBufferHandler, get_log_lines, setup_logging


def test_snapshot_lines_returns_copy():
    handler = LogBufferHandler(capacity=10)
    handler.setFormatter(logging.Formatter("%(message)s"))
    handler.emit(logging.LogRecord("t", logging.INFO, "", 0, "first", (), None))
    handler.emit(logging.LogRecord("t", logging.INFO, "", 0, "second", (), None))

    snapshot = handler.snapshot_lines()
    assert snapshot == ["first", "second"]
    snapshot.append("mutated")
    assert handler.snapshot_lines() == ["first", "second"]


def test_get_log_lines_uses_global_buffer():
    setup_logging("INFO")
    log = logging.getLogger("test_log_buffer_global")
    log.info("hello-buffer")

    lines = get_log_lines()
    assert any("hello-buffer" in line for line in lines)


def test_concurrent_emit_and_snapshot():
    handler = LogBufferHandler(capacity=200)
    handler.setFormatter(logging.Formatter("%(message)s"))
    stop = threading.Event()

    def writer() -> None:
        i = 0
        while not stop.is_set():
            handler.emit(
                logging.LogRecord("t", logging.INFO, "", 0, f"line-{i}", (), None)
            )
            i += 1

    def reader() -> None:
        while not stop.is_set():
            snapshot = handler.snapshot_lines()
            assert isinstance(snapshot, list)
            for line in snapshot:
                assert isinstance(line, str)

    threads = [threading.Thread(target=writer), threading.Thread(target=reader)]
    for thread in threads:
        thread.start()
    stop.set()
    for thread in threads:
        thread.join(timeout=2.0)
        assert not thread.is_alive()

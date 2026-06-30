"""Stream app entry: server or viewer."""

from __future__ import annotations

import sys


def main(argv: list[str] | None = None) -> int:
    argv = list(sys.argv[1:] if argv is None else argv)
    if not argv or argv[0] in ("server", "s"):
        from stream.server import main as server_main

        return server_main()
    if argv[0] in ("viewer", "v", "view"):
        from stream.viewer import main as viewer_main

        return viewer_main()
    print("usage: python -m stream [server|viewer]")
    print("       block-detected-stream          # server")
    print("       block-detected-stream viewer   # LAN viewer")
    return 1


if __name__ == "__main__":
    raise SystemExit(main())

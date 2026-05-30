#!/usr/bin/env python3
"""Capture smoke test for target hardware or image-sequence dev profile.

Examples:
  python scripts/camera_smoke.py --config config/camera.example.json
  python scripts/camera_smoke.py --config config/camera.example.json --save-debug

On Raspberry Pi with CSI camera, switch active_profile to picamera2 in JSON first.
Record `rpicam-hello --list-cameras` or `v4l2-ctl --list-ctrls-menus` for CAM-02 verification.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from block_detected.camera import create_frame_source, load_camera_settings
from block_detected.debug import DebugFrameWriter, DebugSettings


def main() -> int:
    parser = argparse.ArgumentParser(description="Camera capture smoke test")
    parser.add_argument("--config", type=Path, required=True, help="camera JSON config path")
    parser.add_argument("--frames", type=int, default=1, help="frames to capture")
    parser.add_argument("--save-debug", action="store_true", help="write first frame to debug dir")
    args = parser.parse_args()

    settings = load_camera_settings(args.config)
    source = create_frame_source(settings)
    source.start()
    debug_writer = None
    if args.save_debug and settings.debug:
        debug_writer = DebugFrameWriter(
            DebugSettings.from_mapping(
                settings.debug,
                allowed_root=Path.cwd().resolve(),
            )
        )

    try:
        for _ in range(args.frames):
            frame = source.read()
            print(
                json.dumps(
                    {
                        "frame_id": frame.frame_id,
                        "shape": list(frame.image_bgr.shape),
                        "source": frame.source,
                        "metadata": dict(frame.metadata),
                    },
                    indent=2,
                )
            )
            if debug_writer is not None:
                debug_writer.write(frame)
    except Exception as exc:
        print(f"capture failed: {exc}", file=sys.stderr)
        return 1
    finally:
        source.stop()

    return 0


if __name__ == "__main__":
    raise SystemExit(main())

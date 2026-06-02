"""Image folder I/O — batch inference input (expansion stub)."""

from pathlib import Path

IMAGE_EXTENSIONS = {".jpg", ".jpeg", ".png", ".bmp", ".webp"}


def iter_image_paths(directory: str | Path) -> list[Path]:
    """Return sorted image paths from a directory. Used by future apps/batch/."""
    input_dir = Path(directory)
    if not input_dir.is_dir():
        return []
    return [p for p in sorted(input_dir.iterdir()) if p.suffix.lower() in IMAGE_EXTENSIONS and p.is_file()]

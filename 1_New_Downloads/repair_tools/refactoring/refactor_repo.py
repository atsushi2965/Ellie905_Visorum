#!/usr/bin/env python3
"""
Refactor yt-dlp repository layout to per-video directories.

Before:
    yt-dlp/<category>/*.mp4 + *.vtt + *.json + ...

After:
    yt-dlp/<category>/<video_id>/*

- Uses video ID as directory name
- Preserves filenames exactly
- Skips '1 New Downloads'
- Safe to re-run
"""

from pathlib import Path
import re
import shutil
from collections import defaultdict

# -------------------- CONFIG --------------------

YT_DLP_ROOT = Path(__file__).resolve().parent.parent.parent.parent
SKIP_DIRS = {"1 New Downloads"}

# Conservative YouTube ID regex (11 chars)
VIDEO_ID_RE = re.compile(r"\[([A-Za-z0-9_-]{11})\]")

# -------------------- LOGIC --------------------

def extract_video_id(name: str) -> str | None:
    """
    Extract a YouTube video ID from a filename.
    Returns the first plausible ID found, or None.
    """
    matches = VIDEO_ID_RE.findall(name)
    return matches[0] if matches else None


def process_category(category_path: Path) -> None:
    print(f"\n== Processing category: {category_path.name}")

    files_by_id: dict[str, list[Path]] = defaultdict(list)

    for item in category_path.iterdir():
        if item.is_dir():
            # Already migrated or unrelated folder → skip
            continue

        video_id = extract_video_id(item.name)
        if not video_id:
            print(f"  ! No video ID found, skipping: {item.name}")
            continue

        files_by_id[video_id].append(item)

    for video_id, files in files_by_id.items():
        target_dir = category_path / video_id
        target_dir.mkdir(exist_ok=True)

        for file_path in files:
            dest = target_dir / file_path.name
            if dest.exists():
                print(f"  = Exists, skipping: {dest}")
                continue

            print(f"  → Moving {file_path.name} → {target_dir.name}/")
            shutil.move(str(file_path), str(dest))


def main() -> None:
    if not YT_DLP_ROOT.exists():
        raise RuntimeError(f"Root path does not exist: {YT_DLP_ROOT}")

    for category in YT_DLP_ROOT.iterdir():
        if not category.is_dir():
            continue

        if category.name in SKIP_DIRS:
            print(f"\n== Skipping directory: {category.name}")
            continue

        process_category(category)


if __name__ == "__main__":
    main()

#!/usr/bin/env python3
"""
Repair yt-dlp JSON sidecar filenames by injecting video_id.

Renames:
    Original Name.json
→   Original Name [VIDEO_ID].json

- Reads top-level "id" field from JSON
- Skips files that already contain an ID
- Skips '1 New Downloads'
- Safe to re-run
"""

from pathlib import Path
import json
import re

# -------------------- CONFIG --------------------

YT_DLP_ROOT = Path(__file__).resolve().parent.parent.parent.parent
SKIP_DIRS = {"1 New Downloads"}

VIDEO_ID_RE = re.compile(r"\[([A-Za-z0-9_-]{11})\]")

# -------------------- LOGIC --------------------

def filename_has_video_id(name: str) -> bool:
    return bool(VIDEO_ID_RE.search(name))


def process_category(category_path: Path) -> None:
    print(f"\n== Processing category: {category_path.name}")

    for item in category_path.iterdir():
        if not item.is_file():
            continue

        if item.suffix.lower() != ".json":
            continue

        if filename_has_video_id(item.name):
            print(f"  = Already has ID, skipping: {item.name}")
            continue

        try:
            with item.open("r", encoding="utf-8") as f:
                data = json.load(f)
        except Exception as e:
            print(f"  ! Failed to read JSON, skipping: {item.name} ({e})")
            continue

        video_id = data.get("id")
        if not isinstance(video_id, str):
            print(f"  ! No valid 'id' field, skipping: {item.name}")
            continue

        new_name = f"{item.stem} [{video_id}]{item.suffix}"
        new_path = item.with_name(new_name)

        if new_path.exists():
            print(f"  ! Target exists, skipping: {new_name}")
            continue

        print(f"  → Renaming {item.name} → {new_name}")
        item.rename(new_path)


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

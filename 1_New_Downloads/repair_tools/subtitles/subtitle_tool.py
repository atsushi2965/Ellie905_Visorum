#!/usr/bin/env python3

import json
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent.parent.parent
SKIP_DIRS = {"1 New Downloads"}

SUB_LANG = "en"
SUB_EXT = ".vtt"

SKIPPED = []


def find_metadata_json(video_dir: Path, video_id: str) -> Path | None:
    """
    Find the metadata JSON assumed to be named *[<video_id>].json
    """
    for file in video_dir.iterdir():
        if file.suffix == ".json" and f"[{video_id}]" in file.name:
            return file
    return None


def subtitles_exist(video_dir: Path, video_id: str) -> bool:
    """
    Check for any English VTT subtitle containing the video ID.
    """
    for file in video_dir.iterdir():
        if (
            file.is_file()
            and file.suffix == SUB_EXT
            and f".{SUB_LANG}." in file.name
            and f"[{video_id}]" in file.name
        ):
            return True
    return False


def fetch_subtitles(video_dir: Path, url: str, video_id: str) -> bool:
    """
    Invoke yt-dlp to fetch subtitles only
    """
    cmd = [
        "yt-dlp",
        "--cookies-from-browser", "firefox",
        "--skip-download",
        "--write-subs",
        "--write-auto-subs",
        "--sub-langs", SUB_LANG,
        "--sub-format", "vtt",
        "-o", "%(title)s [%(id)s].%(ext)s",
        url,
    ]

    subprocess.run(cmd, cwd=video_dir, check=False)

    return subtitles_exist(video_dir, video_id)


def process_video_dir(video_dir: Path):
    video_id = video_dir.name

    if subtitles_exist(video_dir, video_id):
        print(f"    ✓ Subtitles already exist for {video_id}")
        return

    meta_json = find_metadata_json(video_dir, video_id)
    if not meta_json:
        print(f"    ⚠️  No metadata JSON found for {video_id}")
        SKIPPED.append(f"No metadata found for: {video_id}")
        return

    try:
        with meta_json.open("r", encoding="utf-8") as f:
            data = json.load(f)
    except Exception as e:
        print(f"    ❌ Failed to read JSON for {video_id}: {e}")
        return

    url = data.get("webpage_url")
    if not url:
        print(f"    ⚠️  No webpage_url in JSON for {video_id}")
        return

    print(f"    ⬇ Fetching subtitles for {video_id}")
    if not fetch_subtitles(video_dir, url, video_id):
        SKIPPED.append(f"yt-dlp failure, skipped: {video_id}")


def main():
    for category_dir in ROOT.iterdir():
        if not category_dir.is_dir():
            continue
        if category_dir.name in SKIP_DIRS:
            continue

        print(f"\nProcessing category: {category_dir.name}")

        for video_dir in category_dir.iterdir():
            if not video_dir.is_dir():
                continue

            process_video_dir(video_dir)

    for video in SKIPPED:
        print(video)


if __name__ == "__main__":
    main()

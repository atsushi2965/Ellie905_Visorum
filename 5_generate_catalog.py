#!/usr/bin/env python3
"""
YouTube video catalog generator (Pipeline Step 5)

Outputs (if and only if no failures):
- catalog.json (canonical)
- catalog.html (derived)
"""

import json
import re
import sys
import subprocess
from pathlib import Path
from datetime import datetime
from glob import escape

# ---------------------------
# Configuration
# ---------------------------

VIDEO_EXTENSIONS = {".mp4", ".mkv", ".webm"}
IMG_EXTENSIONS = {".jpg", ".jpeg"}
VIDEO_ID_REGEX = re.compile(r"\[([A-Za-z0-9_-]{11})\]")

EXCLUDE_FOLDERS = {"1_New_Downloads"}
CATALOG_JSON_NAME = "catalog.json"
CATALOG_MD_NAME = "catalog.md"
FAIL_LOG_NAME = "index_fails.txt"

# ---------------------------
# Helpers
# ---------------------------

def is_video_file(path: Path) -> bool:
    return path.is_file() and path.suffix.lower() in VIDEO_EXTENSIONS


def extract_video_id(filename: str) -> str:
    match = VIDEO_ID_REGEX.search(filename)
    if not match:
        raise ValueError("Could not find YouTube video ID in filename")
    return match.group(1)


def normalize_path(path: Path) -> str:
    return path.as_posix()


def load_json(path: Path) -> dict | None:
    try:
        with path.open("r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return None


def pick_thumbnail(candidates: list[Path]) -> Path | None:
    """
    Deterministically choose a thumbnail.
    Preference order:
    1. .jpg / .jpeg
    2. .webp
    """
    if not candidates:
        return None

    for ext in IMG_EXTENSIONS:
        for p in candidates:
            if p.suffix.lower() == ".webp":
                print(".webp\n")
            if p.suffix.lower() == ext:
                return p

    return None


def resolve_thumbnail(video_dir: Path, video_path: Path, video_id: str) -> str:
    """
    Thumbnail resolution order:
    1. * [<id>].jpg
    2. * [<id>].thumb.jpg
    3. Download missing thumbnail (mp4 only)
    4. Download missing thumbnail (mkv only)
    5. Fallback placeholder
    """
    escaped_id = escape(f"[{video_id}]")

    # 1. Exact sidecar
    jpg1 = next(video_dir.glob(f"* {escaped_id}.jpg"), None)
    if jpg1:
        return normalize_path(jpg1)

    # 2. yt-dlp thumb sidecar
    jpg2 = next(video_dir.glob(f"* {escaped_id}.thumb.jpg"), None)
    if jpg2:
        return normalize_path(jpg2)
   
    # 3. MP4
    if video_path.suffix.lower() == ".mp4":
        try:
            subprocess.run(
                [
                    "yt-dlp",
                    "--skip-download",
                    "--convert-thumbnails", "jpg",
                    "--write-thumbnail",
                    "-P", str(video_dir),
                    "--", video_id,
                ],
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
                check=True,
            )

            for p in video_dir.iterdir():
                if escaped_id in p.name and p.suffix.lower == ".jpg":
                    thumb = p

            if thumb:
                return normalize_path(thumb)
        except Exception as e:
            print(f"[WARN] ffmpeg thumbnail backfill failed for {video_id}: {e}")
            pass

    # 4. MKV
    if video_path.suffix.lower() == ".mkv":
        try:
            subprocess.run(
                [
                    "yt-dlp",
                    "--skip-download",
                    "--convert-thumbnails", "jpg",
                    "--write-thumbnail",
                    "-P", str(video_dir),
                    "--", video_id,
                ],
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
                check=True,
            )

            for p in video_dir.iterdir():
                if escaped_id in p.name and p.suffix.lower == ".jpg":
                    thumb = p

            if thumb:
                return normalize_path(thumb)

        except Exception as e:
            print(f"[WARN] yt-dlp thumbnail backfill failed for {video_id}: {e}")
            pass

    return ""  # fallback

# ---------------------------
# Core logic
# ---------------------------

def main() -> int:
    script_dir = Path(__file__).resolve().parent
    repo_root = script_dir.parent

    failures: list[str] = []
    videos: dict[str, dict] = {}

    for genre_dir in sorted(p for p in repo_root.iterdir() if p.is_dir() and p.name not in EXCLUDE_FOLDERS):
        genre = genre_dir.name

        for video_dir in sorted(p for p in genre_dir.iterdir() if p.is_dir()):
            video_files = [p for p in video_dir.iterdir() if is_video_file(p)]
            json_files = [p for p in video_dir.iterdir() if p.suffix == ".json"]

            if not video_files:
                error = str(video_dir)
                error = error + " - No video file detected"
                failures.append(error)
                continue

            if not json_files:
                error = str(video_dir.relative_to(repo_root), " - No JSON sidecar detected")
                failures.append(error)
                continue

            video_path = sorted(video_files)[0]
            sidecar_path = sorted(json_files)[0]

            try:
                video_id = extract_video_id(video_path.name)
            except ValueError:
                error = str(video_path.name + " - No video id extracted from file path")
                failures.append(error)
                continue

            sidecar_data = load_json(sidecar_path)
            if not sidecar_data:
                error = str(video_path.name + " - No data loaded from JSON")
                failures.append(error)
                continue

            title = sidecar_data.get("title")
            uploader = sidecar_data.get("uploader") or sidecar_data.get("channel")
            upload_date = sidecar_data.get("upload_date")
            duration = sidecar_data.get("duration_seconds")
            view_count = sidecar_data.get("view_count")
            description = sidecar_data.get("description")
            tags = sidecar_data.get("tags")
            categories = sidecar_data.get("categories")

            if not title:
                error = str(video_path.name + " - Title missing from JSON")
                failures.append(error)
                continue

            if not uploader:
                error = str(video_path.name + " - Uploader missing from JSON")
                failures.append(error)
                continue

            thumbnail = resolve_thumbnail(video_dir, video_path, video_id)

            videos[video_id] = {
                "id": video_id,
                "title": title,
                "uploader": uploader,
                "upload_date": upload_date,
                "duration": duration,
                "view_count": view_count,
                "description": description,
                "tags": tags,
                "categories": categories,
                "genre": genre,
                "path": normalize_path(video_path.relative_to(repo_root)),
                "thumbnail": thumbnail,
            }

    fail_log = script_dir / FAIL_LOG_NAME
    if failures:
        fail_count = len(failures)
        response = input(
            f"{fail_count} failure(s) detected.\n"
            "1 = Generate catalog anyway (failed videos excluded)\n"
            "2 = write fail log and exit for repair (no catalog)\n"
            "Choice [1/2]: "
        ).strip()

        if str(response) == "2":
            with fail_log.open("w", encoding="utf-8") as f:
                for item in sorted(failures):
                    f.write(item + "\n")
                print(f"Failures written to {fail_log}\nExiting...")
            return 1
        elif str(response) != "1":
            print("Invalid input, defaulting to option 1.")

    if fail_log.exists():
        fail_log.unlink()

    by_genre = {}
    by_uploader = {}

    for vid, record in videos.items():
        by_genre.setdefault(record["genre"], []).append(vid)
        by_uploader.setdefault(record["uploader"], []).append(vid)

    for index in (by_genre, by_uploader):
        for key in index:
            index[key].sort()

    catalog_json = {
        "generated_at": datetime.utcnow().isoformat() + "Z",
        "videos": dict(sorted(videos.items())),
        "by_genre": dict(sorted(by_genre.items())),
        "by_uploader": dict(sorted(by_uploader.items())),
    }

    with (script_dir / CATALOG_JSON_NAME).open("w", encoding="utf-8") as f:
        json.dump(catalog_json, f, indent=2)

    # ---------------------------
    # Write catalog.md (deprecated)
    # ---------------------------

    # 2026-15-01
    # Code below works, but isn't super useful (to me)

#    md_path = script_dir / CATALOG_MD_NAME
#    with md_path.open("w", encoding="utf-8") as f:
#        f.write("# Video Catalog\n\n")
#
#        f.write("## Videos by Genre\n\n")
#        for genre in sorted(by_genre):
#            f.write(f"### {genre}\n\n")
#            for vid in by_genre[genre]:
#                v = videos[vid]
#                f.write(
#                    f"- **{v['title']}**\n"
#                    f"  Uploader: {v['uploader']}\n"
#                    f"  Uploaded: {v['upload_date']}\n"
#                    f"  Duration: {v['duration']}s\n"
#                    f"  [Watch](../{v['path']})\n\n"
#                )
#
#        f.write("## Videos by Uploader\n\n")
#        for uploader in sorted(by_uploader):
#            f.write(f"### {uploader}\n\n")
#            for vid in by_uploader[uploader]:
#                v = videos[vid]
#                f.write(
#                    f"- **{v['title']}** ({v['genre']})\n"
#                    f"  Uploaded: {v['upload_date']}\n"
#                    f"  Duration: {v['duration']}s\n"
#                    f"  [Watch](../{v['path']})\n\n"
#                )

    print("[OK] Catalog generated successfully.")
    return 0


if __name__ == "__main__":
    sys.exit(main())

#!/usr/bin/env python3

import json
import re
import subprocess
import sys
from pathlib import Path
from datetime import datetime

VIDEO_ID_REGEX = re.compile(r"\[([A-Za-z0-9_-]{11})\]")

# -----------------------------
# Utilities
# -----------------------------

def extract_video_id(filename: str) -> str:
    match = VIDEO_ID_REGEX.search(filename)
    if not match:
        raise ValueError("Could not find YouTube video ID in filename")
    return match.group(1)

def sanitize_filename(name: str) -> str:
    return re.sub(r'[\\/:*?"<>|]', "_", name).strip()

# -----------------------------
# Metadata
# -----------------------------

def fetch_metadata_cookies(video_id: str) -> dict:
    url = f"https://www.youtube.com/watch?v={video_id}"

    cookies = Path(__file__).parent.resolve()
    cookies = cookies / Path("cookies.firefox-private.txt")

    result = subprocess.run(
        ["yt-dlp", "-j", "--cookies", cookies, url],
        capture_output=True,
        text=True
    )

    if result.returncode != 0:
        raise RuntimeError(f"attempted yt-dlp with cookies, failed:\n{result.stderr}")

    return json.loads(result.stdout)

def fetch_metadata(video_id: str) -> dict:
    url = f"https://www.youtube.com/watch?v={video_id}"

    #, "--cookies-from-browser", "firefox",
    result = subprocess.run(
        ["yt-dlp", "-j", url],
        capture_output=True,
        text=True
    )

    if "cookies" in result.stderr.lower(): # Age-restriction
        return fetch_metadata_cookies(video_id)

    if result.returncode != 0:
        raise RuntimeError(f"yt-dlp failed:\n{result.stderr}")

    return json.loads(result.stdout)

def write_json_sidecar(video_path: Path, metadata: dict):
    """
    Write a curated, archival-grade JSON sidecar.
    Intentionally excludes yt-dlp extractor noise.
    """

    upload_date = metadata.get("upload_date")  # YYYYMMDD
    year = upload_date[:4] if upload_date else None
    date_str = datetime.now().strftime("%Y%m%d")

    archival = {
        "id": metadata.get("id"),
        "title": metadata.get("title"),
        "uploader": metadata.get("uploader"),
        "uploader_id": metadata.get("uploader_id"),
        "channel_url": metadata.get("channel_url"),
        "upload_date": upload_date,
        "view_count": metadata.get("view_count"),
        "view_count_date": date_str,
        "year": year,
        "duration_seconds": metadata.get("duration"),
        "description": metadata.get("description"),
        "tags": metadata.get("tags"),
        "categories": metadata.get("categories"),
        "language": metadata.get("language"),
        "webpage_url": metadata.get("webpage_url"),
        "original_filename": video_path.name,
        "extracted_by": "yt-dlp",
        "extractor_version": metadata.get("extractor_version"),
    }

    # Remove empty fields cleanly
    archival = {k: v for k, v in archival.items() if v is not None}

    safe_title = sanitize_filename(archival.get("title", video_path.stem))
    video_id = metadata.get("id")
    json_path = video_path.with_name(f"{safe_title} [{video_id}].json")

    with open(json_path, "w", encoding="utf-8") as f:
        json.dump(archival, f, ensure_ascii=False, indent=2)

    print(f"Curated JSON sidecar written: {json_path.name}")


# -----------------------------
# Tagging (WebM-safe)
# -----------------------------

def embed_metadata_webm(video_path: Path, metadata: dict):
    upload_date = metadata.get("upload_date")  # YYYYMMDD
    title = metadata.get("title")
    uploader = metadata.get("uploader")

    ffmpeg_cmd = [
        "ffmpeg", "-y",
        "-i", str(video_path),
    ]

    if upload_date:
        year = upload_date[:4]
        ffmpeg_cmd += ["-metadata", f"date={upload_date}"]
        ffmpeg_cmd += ["-metadata", f"year={year}"]

    if title:
        ffmpeg_cmd += ["-metadata", f"title={title}"]

    if uploader:
        ffmpeg_cmd += ["-metadata", f"artist={uploader}"]

    temp_out = video_path.with_suffix(".tagged" + video_path.suffix)
    ffmpeg_cmd += ["-map_metadata", "0", "-c", "copy", str(temp_out)]

    subprocess.run(ffmpeg_cmd, check=True)
    temp_out.replace(video_path)

    print("Embedded WebM metadata successfully")

# -----------------------------
# Main
# -----------------------------

def main():
    if len(sys.argv) != 2:
        print("Usage: tag_youtube_video.py <video_file>")
        sys.exit(1)

    video_path = Path(sys.argv[1])
    if not video_path.exists():
        raise FileNotFoundError(video_path)

    video_id = extract_video_id(video_path.name)
    print(f"Video ID: {video_id}")

    metadata = fetch_metadata(video_id)

    #embed_metadata_webm(video_path, metadata)
    write_json_sidecar(video_path, metadata)

    print("Archival tagging complete.")

if __name__ == "__main__":
    main()

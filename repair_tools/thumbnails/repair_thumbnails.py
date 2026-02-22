from pathlib import Path
import re
import subprocess
import sys
import shutil
import tempfile

# 2025-12-20 and 21
# I didn't use the correct yt-dlp commands to download the first 300 videos with
# thumbnails attached. Instead of redownloading, I had chatgpt make this to
# process the videos and attach the thumbnail depending on container type.
# In the future, every video regardless of type should have a thumbnail file


ROOT = Path.cwd()
MANIFEST = ROOT / "manifest.txt"
URLS = ROOT / "urls.txt"

YOUTUBE_PREFIX = "https://www.youtube.com/watch?v="

VIDEO_EXTS = {".mkv", ".mp4", ".webm"}

ID_PATTERN = re.compile(r"\[([A-Za-z0-9_-]{11})\]")


def extract_ids_from_manifest():
    ids = []
    with MANIFEST.open("r", encoding="utf-8") as f:
        for line in f:
            match = ID_PATTERN.search(line)
            if match:
                ids.append(match.group(1))
    return ids


def generate_urls_txt():
    ids = extract_ids_from_manifest()
    if not ids:
        raise RuntimeError("No video IDs found in manifest.txt")

    with URLS.open("w", encoding="utf-8") as f:
        for vid in ids:
            f.write(f"{YOUTUBE_PREFIX}{vid}\n")

    print(f"Generated urls.txt with {len(ids)} entries")


def load_urls():
    with URLS.open("r", encoding="utf-8") as f:
        return [line.strip() for line in f if line.strip()]


def find_video_file(video_id):
    matches = []
    for path in ROOT.rglob("*"):
        if path.suffix.lower() in VIDEO_EXTS and f"[{video_id}]" in path.name:
            matches.append(path)

    if len(matches) == 0:
        raise FileNotFoundError(f"No local video found for ID {video_id}")
    if len(matches) > 1:
        raise RuntimeError(f"Multiple videos found for ID {video_id}: {matches}")

    return matches[0]


def download_thumbnail(url, workdir):
    cmd = [
        "yt-dlp",
        "--skip-download",
        "--write-thumbnail",
        "--convert-thumbnails", "jpg",
        url,
    ]
    subprocess.run(cmd, cwd=workdir, check=True)


def embed_thumbnail_mp4(video_path: Path, thumb_path: Path):
    cmd = [
        "atomicparsley",
        str(video_path),
        "--artwork", str(thumb_path),
        "--overWrite",
    ]
    subprocess.run(cmd, check=True)


def embed_thumbnail_mkv(video_path: Path, thumb_path: Path):
    with tempfile.NamedTemporaryFile(
        suffix=".mkv",
        dir=video_path.parent,
        delete=False
    ) as tmp:
        tmp_path = Path(tmp.name)

    cmd = [
        "ffmpeg", "-y",
        "-i", str(video_path),
        "-attach", str(thumb_path),
        "-map", "0:v:0",
        "-map", "0:a?",
        "-map", "0:s?",
        "-c", "copy",
        "-metadata:s:t", "mimetype=image/jpeg",
        "-metadata:s:t", "filename=cover.jpg",
        "-movflags", "+faststart",
        str(tmp_path),
    ]

    subprocess.run(cmd, check=True)
    tmp_path.replace(video_path)


def process_video(url):
    video_id = url.split("v=")[-1]
    video_path = find_video_file(video_id)

    print(f"Processing {video_path.name}")

    # Download thumbnail into same directory
    download_thumbnail(url, video_path.parent)

    # Find the downloaded thumbnail
    thumbs = list(video_path.parent.glob(f"*{video_id}*.jpg"))
    if not thumbs:
        raise RuntimeError(f"No thumbnail downloaded for {video_id}")

    thumb = thumbs[0]

    if video_path.suffix.lower() == ".webm":
        # Sidecar only
        sidecar = video_path.with_name(
        video_path.stem + ".thumb" + thumb.suffix
        )

        if sidecar.exists():
            print("  Sidecar thumbnail already exists, skipping")
            thumb.unlink()
            return

        thumb.rename(sidecar)
        print(f"  Saved sidecar thumbnail: {sidecar.name}")

    else:
        ext = video_path.suffix.lower()

        if ext == ".mp4":
            print("  Embedding thumbnail into MP4 (AtomicParsley)")
            embed_thumbnail_mp4(video_path, thumb)

        elif ext == ".mkv":
            print("  Embedding thumbnail into MKV (ffmpeg attached_pic)")
            embed_thumbnail_mkv(video_path, thumb)

        else:
            raise RuntimeError(f"Unsupported container for embedding: {ext}")

        thumb.unlink()


def main():
    if not URLS.exists():
        print("urls.txt not found, generating from manifest.txt")
        generate_urls_txt()

    urls = load_urls()

    for url in urls:
        try:
            process_video(url)
        except Exception as e:
            print(f"ERROR processing {url}: {e}", file=sys.stderr)


if __name__ == "__main__":
    main()

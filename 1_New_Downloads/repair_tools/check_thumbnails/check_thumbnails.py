#!/usr/bin/env python3
import json
from pathlib import Path

# --- PATHS ---
ROOT = Path(__file__).resolve().parent.parent.parent
CATALOG_PATH = ROOT / "catalog.json"

# --- LOAD ---
with CATALOG_PATH.open("r", encoding="utf-8") as f:
    catalog = json.load(f)

videos = catalog.get("videos", {})

if not isinstance(videos, dict):
    raise TypeError("catalog['videos'] is not a dict — catalog format mismatch")

checked = 0
ignored_empty = 0
missing = []

# --- CHECK ---
for video_id, entry in videos.items():
    thumb = entry.get("thumbnail", "")

    if not thumb:
        ignored_empty += 1
        continue

    checked += 1
    thumb_path = Path(thumb)

    # thumbnails in your catalog are absolute, but this keeps it safe
    if not thumb_path.is_absolute():
        thumb_path = (ROOT / thumb_path).resolve()

    if not thumb_path.exists():
        missing.append({
            "id": video_id,
            "title": entry.get("title", "<no title>"),
            "thumbnail": str(thumb_path),
        })

# --- REPORT ---
print(f"Thumbnails checked : {checked}")
print(f"Ignored empty       : {ignored_empty}")
print(f"Missing thumbnails  : {len(missing)}")

if missing:
    print("\nMissing thumbnail files:")
    for m in missing:
        print(f"- {m['title']} ({m['id']})")
        print(f"  {m['thumbnail']}")

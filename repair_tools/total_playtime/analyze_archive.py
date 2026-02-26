#!/usr/bin/env python3

"""
===========================================================
VISORUM ARCHIVE ANALYZER
-----------------------------------------------------------
Single-pass statistics generator for catalog.json
Relative path: ../../catalog.json
===========================================================
"""

# ========================
# IMPORTS
# ========================
import json
import heapq
from collections import defaultdict
from pathlib import Path


# ========================
# CONSTANTS
# ========================
CATALOG_PATH = Path("../../catalog.json")
TOP_N = 5


# ========================
# HELPERS
# ========================
def format_duration(seconds: int) -> str:
    """Convert seconds → H:M:S"""
    hours = seconds // 3600
    minutes = (seconds % 3600) // 60
    secs = seconds % 60
    return f"{hours}h {minutes}m {secs}s"


def push_top(heap, item, max_size=TOP_N):
    """
    Maintain a fixed-size min-heap for top N values.
    Stores (view_count, title)
    """
    if len(heap) < max_size:
        heapq.heappush(heap, item)
    else:
        heapq.heappushpop(heap, item)


def push_bottom(heap, item, max_size=TOP_N):
    """
    Maintain fixed-size max-heap for lowest N values.
    We invert view_count so heapq still works as min-heap.
    Stores (-view_count, title)
    """
    inverted = (-item[0], item[1])
    if len(heap) < max_size:
        heapq.heappush(heap, inverted)
    else:
        heapq.heappushpop(heap, inverted)


# ========================
# MAIN
# ========================
def main():
    if not CATALOG_PATH.exists():
        print(f"Catalog file not found at {CATALOG_PATH}")
        return

    with open(CATALOG_PATH, "r", encoding="utf-8") as f:
        data = json.load(f)

    # Allow either list or {"videos": [...]}
    #if isinstance(data, dict):
        #videos = data.get("videos", [])
        #videos = data["videos"]
    #else:
        #videos = data

    # ========================
    # GLOBAL ARCHIVE STATS
    # ========================
    total_videos = 0
    total_duration = 0
    total_views = 0

    tag_counter = defaultdict(int)

    top_videos = []      # min-heap
    bottom_videos = []   # inverted min-heap

    # ========================
    # PER GENRE / UPLOADER
    # ========================
    genre_stats = {}
    uploader_stats = {}

    # ========================
    # SINGLE PASS LOOP
    # ========================
    for video, data in data.get("videos", {}).items():
        total_videos += 1

        title = data.get("title", "UNKNOWN")
        genre = data.get("genre", "UNKNOWN")
        uploader = data.get("uploader", "UNKNOWN")
        duration = int(data.get("duration", 0))
        view_count = int(data.get("view_count", 0))
        tags = data.get("tags", [])

        # ----- Global counters -----
        total_duration += duration
        total_views += view_count

        push_top(top_videos, (view_count, title))
        push_bottom(bottom_videos, (view_count, title))

        for tag in tags:
            tag_counter[tag] += 1

        # ----- Genre stats -----
        if genre not in genre_stats:
            genre_stats[genre] = {
                "count": 0,
                "duration": 0,
                "views": 0,
            }

        genre_stats[genre]["count"] += 1
        genre_stats[genre]["duration"] += duration
        genre_stats[genre]["views"] += view_count

        # ----- Uploader stats -----
        if uploader not in uploader_stats:
            uploader_stats[uploader] = {
                "count": 0,
                "duration": 0,
                "views": 0,
            }

        uploader_stats[uploader]["count"] += 1
        uploader_stats[uploader]["duration"] += duration
        uploader_stats[uploader]["views"] += view_count

    # ========================
    # FINAL COMPUTATIONS
    # ========================
    top_tags = heapq.nlargest(TOP_N, tag_counter.items(), key=lambda x: x[1])

    # Convert bottom heap back
    lowest_videos = [(-v, t) for v, t in bottom_videos]
    lowest_videos.sort()

    top_videos.sort(reverse=True)

    # ========================
    # PRINT RESULTS
    # ========================
    print("\n============================")
    print("FULL ARCHIVE STATS")
    print("============================")
    print(f"Total videos: {total_videos}")
    print(f"Total duration: {format_duration(total_duration)}")
    print(f"Total views: {total_views:,}")
    print(f"Average duration: {format_duration(total_duration // max(total_videos, 1))}")

    print("\nTop 5 Most Viewed:")
    for views, title in top_videos:
        print(f"{views:,} views — {title}")

    print("\nTop 5 Least Viewed:")
    for views, title in lowest_videos:
        print(f"{views:,} views — {title}")

    print("\nTop 5 Tags:")
    for tag, count in top_tags:
        print(f"{tag}: {count}")

    print("\n============================")
    print("PER GENRE")
    print("============================")
    for genre, stats in sorted(genre_stats.items()):
        print(f"\n{genre}")
        print(f"  Videos: {stats['count']}")
        print(f"  Total Duration: {format_duration(stats['duration'])}")
        print(f"  Total Views: {stats['views']:,}")

    #print("\n============================")
    #print("PER UPLOADER")
    #print("============================")
    #for uploader, stats in sorted(uploader_stats.items()):
    #    if stats['count'] >= 3:
    #        print(f"\n{uploader}")
    #        print(f"  Videos: {stats['count']}")
    #        print(f"  Total Duration: {format_duration(stats['duration'])}")
    #        print(f"  Total Views: {stats['views']:,}")


if __name__ == "__main__":
    main()

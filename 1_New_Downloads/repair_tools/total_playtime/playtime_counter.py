import json
import subprocess
import sys
from pathlib import Path
from datetime import datetime

ROOT = Path(__file__).resolve().parent.parent.parent.parent
EXCLUDE_DIR = "1_New_Downloads"
FAIL_LOG = Path("count_failures.txt")


def log_failure(path: Path, reason: str):
    with FAIL_LOG.open("a", encoding="utf-8") as f:
        f.write(f"{path} :: {reason}\n")


def format_time(n: int) -> str:
    secs = n%60
    mins = int(n/60)
    hours = 0
    days = 0
    weeks = 0

    if mins >= 60:
        hours = int(mins/60)
        mins = mins%60

    if hours >= 24:
        days = int(hours/24)
        hours = hours%24

    if days >= 7:
        weeks = int(days/7)
        days = days%7

    time = ""
    if weeks > 0:
        time = time + f"{weeks}w"

    if days > 0:
        time = time + f"{days}d"

    if hours > 0:
        time = time + f"{hours}h"

    if mins > 0:
        time = time + f"{mins}m"

    if secs > 0:
        time = time + f"{secs}s"

    return time


def process_json(path: Path, counter: int):
    try:
        with path.open("r", encoding="utf-8") as f:
            data = json.load(f)
    except Exception:
        log_failure(path, "invalid json")
        print(f"[error] failed to load json: {path}")
        return

    if "duration_seconds" in data:
        time = int(data.get("duration_seconds", 0))
        counter = counter + time

    return counter


def main():
    if FAIL_LOG.exists():
        FAIL_LOG.unlink()

    counter = 0

    for json_path in ROOT.rglob("*.json"):
        if EXCLUDE_DIR in json_path.parts:
            continue
        counter = process_json(json_path, counter)

    time = format_time(counter)

    print(f"duration count before: {counter}")
    print(f"duration count after: {time}")


if __name__ == "__main__":
    main()

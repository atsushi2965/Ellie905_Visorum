# Create a list.txt with every video in your library to share with others

import json
import subprocess
import sys
from pathlib import Path
from datetime import datetime

EXCLUDE_DIR = "1_New_Downloads"
FAIL_LOG = Path("failures.txt")


def log_failure(path: Path, reason: str):
    with FAIL_LOG.open("a", encoding="utf-8") as f:
        f.write(f"{path} :: {reason}\n")


def process_json(path: Path):
    try:
        with path.open("r", encoding="utf-8") as f:
            data = json.load(f)
    except Exception:
        log_failure(path, "invalid json")
        print(f"[error] failed to load json: {path}")
        return

    url = ""

    if "webpage_url" in data:
        url = data.get("webpage_url")

    return url


def main():
    if FAIL_LOG.exists():
        FAIL_LOG.unlink()

    script_dir = Path(__file__).resolve().parent # 1_New_Downloads/repair_tools/full_library_list_text/
    root_dir = script_dir.resolve().parent.parent.parent # yt-dlp

    list_path = Path(script_dir, "list.txt")

    urls = []
    counter = 0

    for json_path in root_dir.rglob("*.json"):
        if EXCLUDE_DIR in json_path.parts:
            continue
        urls.append(str(process_json(json_path)))
        counter = counter + 1

    print(f"{counter} video(s) processed.")

    try:
        with list_path.open("w", encoding="utf-8") as f:
            for url in urls:
                f.write(url + "\n")
    except Exception as e:
        log_failure(path, f"{e}")
        print(f"[error] failed to write list: {list_path}")
        return

    print(f"list.txt written: {list_path}")


if __name__ == "__main__":
    main()

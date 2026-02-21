import json
import subprocess
import sys
from pathlib import Path
from datetime import datetime

ROOT = Path(__file__).resolve().parent.parent.parent.parent
EXCLUDE_DIR = "1_New_Downloads"
FAIL_LOG = Path("view_count_failures.txt")


def log_failure(path: Path, reason: str):
    with FAIL_LOG.open("a", encoding="utf-8") as f:
        f.write(f"{path} :: {reason}\n")


def get_view_count(url: str) -> int | None:
    cmd = [
        "yt-dlp",
        "--cookies-from-browser", "firefox",
        "-j",
        "--no-playlist",
        url
    ]

    try:
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=30
        )
    except Exception as e:
        return None

    if result.returncode != 0:
        return None

    try:
        data = json.loads(result.stdout)
    except json.JSONDecodeError:
        return None

    return data.get("view_count")


def process_json(path: Path):
    try:
        with path.open("r", encoding="utf-8") as f:
            data = json.load(f)
    except Exception:
        log_failure(path, "invalid json")
        print(f"[error] failed to load json: {path}")
        return

    if "view_count" in data:
        return  # idempotent; remove if you want to overwrite

    url = data.get("webpage_url")
    if not url:
        log_failure(path, "missing webpage_url")
        print(f"[error] failed to retrieve url {url}")
        return

    print(f"[info] processing url: {url}")

    view_count = get_view_count(url)
    if view_count is None:
        log_failure(path, "view_count unavailable")
        print(f"[warn] no view count extracted")
        return

    print(f"[info] retrieved view_count: {view_count}")

    data["view_count"] = view_count

    date_str = datetime.now().strftime("%Y%m%d")
    data["view_count_date"] = date_str

    try:
        with path.open("w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
    except Exception as e:
        log_failure(path, "failed to write json")
        print(f"[fatal error] failed to write json: {e}")

    print(f"[info] success!")


def main():
    if FAIL_LOG.exists():
        FAIL_LOG.unlink()

    for json_path in ROOT.rglob("*.json"):
        if EXCLUDE_DIR in json_path.parts:
            continue
        process_json(json_path)


if __name__ == "__main__":
    main()

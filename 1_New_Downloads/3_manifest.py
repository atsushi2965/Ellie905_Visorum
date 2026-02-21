import os
from pathlib import Path
from datetime import datetime

# Recursively find all files in a folder that match certain extensions.
def find_files(root_dir):
    """
    Walk through `root_dir` recursively and yield all files.

    Args:
        root_dir (str or Path): Root directory to search.

    Yields:
        Path: Full path to each file.
    """
    root_dir = Path(root_dir)

    for path in root_dir.rglob("*"):
        if path.is_file():
            yield path

if __name__ == "__main__":
    search_dir = Path(__file__).parent.parent.resolve()
    #print(f"search dir: {search_dir}")

    today = datetime.now().strftime("%Y-%m-%d") # e.g. 2025-12-18
    output_file = Path("manifest.txt")

    print(f"Searching {search_dir} for all files..\n")

    # Collect matches
    matches = list(find_files(search_dir))

    # Write results to file
    with output_file.open("w", encoding="utf-8") as f:
        f.write("Date of creation: " + str(today) + "\n")
        for file_path in matches:
            # Make path relative to search_dir
            relative_path = file_path.relative_to(search_dir)
            f.write(str(relative_path) + "\n")
            #print(str(relative_path))

    print(f"✅ Found {len(matches)} matching files. Saved to {output_file}")

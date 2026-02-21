#!/usr/bin/env bash
# batch_tag_videos.sh
# Batch tag videos inside video_id folders

set -euo pipefail

ROOT_DIR="${1:-.}"

SKIP_DIRS=(
    "old_manifests"
    "repair_tools"
    "_internal"
)

should_skip() {
    local name="$1"
    for skip in "${SKIP_DIRS[@]}"; do
        [[ "$name" == "$skip" ]] && return 0
    done
    return 1
}

# Iterate only over immediate subdirectories
find "$ROOT_DIR" -mindepth 1 -maxdepth 1 -type d -print0 |
while IFS= read -r -d '' dir; do
    dirname="$(basename "$dir")"

    if should_skip "$dirname"; then
        echo "Skipping directory: $dirname"
        continue
    fi

    echo "Entering: $dir"

    find "$dir" -type f \( -iname "*.webm" -o -iname "*.mp4" -o -iname "*.mkv" \) -exec bash -c '
        for file do
            fullpath="$(realpath "$file")"
            echo "Processing: $fullpath"
            python3 2a_tag_youtube_video.py "$fullpath"
            echo "Done: $fullpath"
            echo "-------------------------"
        done
    ' bash {} +

done

echo "Batch tagging complete."

# Generate new manifest file
python3 3_manifest.py

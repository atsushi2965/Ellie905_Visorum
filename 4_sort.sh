#!/usr/bin/env bash

# ============================================================
# VISORUM TOOLS - STEP 4
# Interactive sorter for new yt-dlp downloads
# Script location: yt-dlp/1_New_Downloads/
# ============================================================

set -euo pipefail

BASE_DIR="$(cd "$(dirname "$0")" && pwd)"        # 1_New_Downloads
PARENT_DIR="$(dirname "$BASE_DIR")"              # yt-dlp root

SKIP_FOLDERS=("old_manifests" "repair_tools")

cd "$BASE_DIR"

# ------------------------------------------------------------
# Build category list from parent (exclude 1_New_Downloads)
# ------------------------------------------------------------
mapfile -t CATEGORIES < <(
    find "$PARENT_DIR" -mindepth 1 -maxdepth 1 -type d \
        ! -name "1_New_Downloads" \
        -printf "%f\n" | sort
)

if [[ ${#CATEGORIES[@]} -eq 0 ]]; then
    echo "No category folders found in parent directory $PARENT_DIR. Make some!"
    exit 1
fi

# ------------------------------------------------------------
# Helper: skip internal folders
# ------------------------------------------------------------
should_skip() {
    local name="$1"
    for skip in "${SKIP_FOLDERS[@]}"; do
        [[ "$name" == "$skip" ]] && return 0
    done
    return 1
}

# ------------------------------------------------------------
# Sort loop
# ------------------------------------------------------------
shopt -s nullglob

for VIDEO_PATH in "$BASE_DIR"/*; do
    [[ -d "$VIDEO_PATH" ]] || continue

    VIDEO_NAME="$(basename "$VIDEO_PATH")"

    # Skip internal folders and this script directory entries
    if should_skip "$VIDEO_NAME"; then
        continue
    fi

    echo
    echo "--------------------------------------------------"
    echo "Files in folder:"
    echo "--------------------------------------------------"

    for file in "$VIDEO_PATH"/*; do
        printf "  %s\n" "$(basename "$file")"
    done

    # Show categories
    for i in "${!CATEGORIES[@]}"; do
        printf "%2d. %s\n" "$((i+1))" "${CATEGORIES[$i]}"
    done
    echo " 0. Skip"

    # Input loop
    while true; do
        read -rp "Move to category #: " choice

        [[ -z "$choice" ]] && continue

        if [[ "$choice" == "0" ]]; then
            echo "Skipped."
            break
        fi

        if [[ "$choice" =~ ^[0-9]+$ ]] &&
           (( choice >= 1 && choice <= ${#CATEGORIES[@]} )); then

            TARGET="${CATEGORIES[$((choice-1))]}"
            mv "$VIDEO_PATH" "$PARENT_DIR/$TARGET/"
            echo "Moved to $TARGET/"
            break
        else
            echo "Invalid selection."
        fi
    done
done

# ------------------------------------------------------------
# Post-check for remaining unsorted folders
# ------------------------------------------------------------
REMAINING=0

for VIDEO_PATH in "$BASE_DIR"/*; do
    [[ -d "$VIDEO_PATH" ]] || continue
    VIDEO_NAME="$(basename "$VIDEO_PATH")"

    if should_skip "$VIDEO_NAME"; then
        continue
    fi

    REMAINING=1
    break
done

if (( REMAINING == 1 )); then
    echo "Unsorted videos remain. Exiting before Step 5."
    exit 1
fi

# ------------------------------------------------------------
# Success -> Execute Step 5 from parent
# ------------------------------------------------------------
echo "Sorting complete. Running catalog generator..."
exec python3 "5_generate_catalog.py"

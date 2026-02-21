#!/bin/bash

SCRIPT_DIR="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
URL_FILE="list.txt"
MANIFEST_FILE="manifest.txt"
COOKIE_FILE="$SCRIPT_DIR/cookies.firefox-private.txt"
FAILED_FILE="$SCRIPT_DIR/failed_downloads.txt"
DUPES_FILE="dupes.txt"

> "$FAILED_FILE"
> "$DUPES_FILE"

if [[ ! -f "$URL_FILE" ]]; then
    echo "Error: $URL_FILE not found."
    exit 1
fi

declare -A SEEN_IDS=()

if [[  -f "$MANIFEST_FILE" ]]; then
    echo "$MANIFEST_FILE found. Extracting video IDs.."

    # --- Load existing video IDs from manifest ---
    while IFS= read -r line; do
        if [[ "$line" =~ \[([A-Za-z0-9_-]{11})\] ]]; then
            SEEN_IDS["${BASH_REMATCH[1]}"]=1
        fi
    done < "$MANIFEST_FILE"

    echo "Loaded ${#SEEN_IDS[@]} existing video IDs from manifest."
fi

# --- Process download list ---
while IFS= read -r url; do
    [[ -z "$url" || "$url" =~ ^# ]] && continue

    # Extract video ID from URL using yt-dlp (robust)
    #video_id=$(yt-dlp --cookies-from-browser firefox --get-id "$url" 2>/dev/null)
    video_id=$(yt-dlp --cookies "$COOKIE_FILE" --get-id "$url" 2>/dev/null)

    if [[ -z "$video_id" ]]; then
        echo "Could not extract ID: $url"
        echo "$url" >> "$FAILED_FILE"
        continue
    fi

    if [[ -n "${SEEN_IDS[$video_id]}" ]]; then
        echo "Duplicate found, skipping: $url"
        echo "$url" >> "$DUPES_FILE"
        continue
    fi

    if ! mkdir -p -- "$video_id"; then
        echo "Failed to create folder $video_id, skipping."
        continue
    fi

    cd -- "$video_id" || continue

    echo "Downloading: $url to $video_id"

    #if yt-dlp --cookies-from-browser firefox --embed-metadata --embed-thumbnail "$url"; then
    #--cookies-from-browser firefox \
    #--remote-components ejs:github \
    #--js-runtimes deno:~/.deno/bin/deno \
    if yt-dlp \
        -f "bv*[ext=mp4]+ba*[ext=m4a]/b[ext=mp4]/bv*+ba/b" \
        --cookies "$COOKIE_FILE" \
        --write-thumbnail \
        --convert-thumbnails jpg \
        --embed-thumbnail \
        --embed-metadata \
        --write-subs \
        --write-auto-subs \
        --sub-langs en \
        --sub-format vtt \
        -o "%(title)s [%(id)s].%(ext)s" \
        "$url";
    then
        SEEN_IDS["$video_id"]=1
    else
        echo "Failed: $url"
        echo "$url" >> "$FAILED_FILE"
    fi

    cd $SCRIPT_DIR

done < "$URL_FILE"

echo "All downloads finished."
[[ -s "$FAILED_FILE" ]] && echo "Some downloads failed. See $FAILED_FILE."
[[ -s "$DUPES_FILE" ]] && echo "Duplicates logged to $DUPES_FILE."

./2_batch_tag_videos.sh

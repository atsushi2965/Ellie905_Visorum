# <img src="visorum.ico" width="32" height="32"> Visorum Archival Tooling

This repository contains a **YouTube archival pipeline** built around `yt-dlp`, Bash, and Python.

It is designed to create a **portable, self-contained video archive** with:
- A strict and predictable directory structure
- Per-video metadata sidecars
- Repair and backfill tooling
- A machine-readable catalog for external browsers (such as Visorum GUI)

This documentation is for **users of the archival tools**, not contributors.

---

## Core Concepts

- Each video is identified by its **YouTube video ID**
- Each video exists in **exactly one category**
- Metadata is stored as **JSON sidecars** (same name as the video file but .json)
- The archive is **fully portable** if structure rules are respected (listed below)
- Core tools are **idempotent** where possible

---

## Prerequisites

All tools assume a Linux environment.
Windows users should use **WSL** or Git Bash.

### Required Software

#### Bash
Used to orchestrate the pipeline.

```bash
bash --version
```

Most Linux and macOS systems already include Bash.

---

#### Python 3

Required for metadata tagging, catalog generation, and GUI support. (not required for downloads)

```bash
python3 --version
```

Install if missing:

**Ubuntu / Mint / Debian**

```bash
sudo apt update
sudo apt install python3 python3-pip python3-venv -y
```

**Fedora**

```bash
sudo dnf install python3 python3-pip python3-virtualenv -y
```

**Arch / Manjaro / Garuda**

```bash
sudo pacman -S python python-pip python-virtualenv
```

---

#### ffmpeg

Required for media processing and thumbnail handling.

```bash
ffmpeg -version
```

Install if missing:

**Ubuntu / Mint / Debian**

```bash
sudo apt install ffmpeg -y
```

**Fedora**

```bash
sudo dnf install ffmpeg -y
```

**Arch / Manjaro / Garuda**

```bash
sudo pacman -S ffmpeg
```

---

#### Deno

Used by auxiliary tooling. (only for YouTube downloads)

```bash
deno --version
```

Install:

```bash
curl -fsSL https://deno.land/install.sh | sh
```

Follow the output instructions to add Deno to your `PATH`.

---

#### yt-dlp (Pinned Binary Recommended)

The pipeline was built and tested against a specific `yt-dlp` version.
**Do not rely on distro-packaged yt-dlp**, which is often outdated.

Download the official binary:

```bash
curl -L https://github.com/yt-dlp/yt-dlp/releases/latest/download/yt-dlp -o yt-dlp
sudo mv yt-dlp /usr/local/bin/
sudo chmod +x /usr/local/bin/yt-dlp
yt-dlp --version
```

Placing it in `/usr/local/bin` ensures it takes precedence over `/usr/bin`.

---

## Archive Structure

The tools expect the following structure:

```
yt-dlp/
├── 1_New_Downloads/
│   ├── repair_tools/
│   └── <main_tools>
├── <category_name>/
│   └── <video_id>/
│       ├── <video file>
│       ├── <thumbnail>
│       ├── <subtitles>
│       └── <video_json>
```

### Rules

* One folder per video, named **exactly** as the video ID (not strict, but very long paths may break on some systems)
* One category per video (one video in two categories may appear duplicated in gui browser)
* Category name equals folder name
* Videos left in `1_New_Downloads` are **ignored** during Step 5 and won't appear in the gui browser
* The Visorum gui browser looks for a folder called 'yt-dlp'

If these rules are followed, all tools will function correctly.

---

## Pipeline Overview

### Step 0: Collect URLs

Copy a URL to download such as `https://www.youtube.com/watch?v=dQw4w9WgXcQ` and paste it into `yt-dlp/1_New_Downloads/list.txt` or use

`echo "<url>" >> list.txt` 

to append url to bottom of list (if it already has urls). I personally made a "add_video 'URL'" function to my config to do this for me from any location.

Anything after the 'watch?v=<video_id>' section (such as ?list=) can produce unwanted results (such as downloading an entire playlist).

--- 

### Step 1: Download

Downloads raw media and sidecars from URLs in `list.txt`.

Run from inside `1_New_Downloads`:

```bash
./1_download_multiple.sh
```

* Failed downloads → `failed_downloads.txt`
* Duplicate IDs → `dupes.txt`
* Existing videos are skipped using the manifest

Steps 2 and 3 trigger automatically unless interrupted.

---

### Step 1 Alt: Age-Restricted Downloads

Downloads from YouTube with cookies is not recommended by yt-dlp generally, as it can lead to actions being taken on your YouTube account. That said, it is possible.

YT-DLP's Official Instructions are listed [here](https://github.com/yt-dlp/yt-dlp/wiki/Extractors#exporting-youtube-cookies)

TL-DR:

* Log in to YouTube from a private/incognito window, navigate to 'https://www.youtube.com/robots.txt'
* I used the cookie.txt extension for Firefox to extract a minimal working cookies file **Warning: This is not risk-free, you assume responsibility for using external apps and giving them your credentials, and following website TOS** 
* Rename the cookies file according to `1_download_multiple_cookies.sh`, "cookies.firefox-private.txt"
* Use `1_download_multiple_cookies.sh` instead of the regular downloader

Recommended: Download all videos that don't require cookies first, failed downloads will appear in `failed_downloads.txt`. Just delete list.txt and rename the failed downloads list to `list.txt`, then rerun with cookies.

---

### Step 2: Tagging (Metadata Pass)

By default this is ran automatically by Step 1.

* Scans `1_New_Downloads`
* Rebuilds URLs from video IDs
* Extracts structured metadata via `yt-dlp`
* Writes normalized JSON sidecars

---

### Step 3: Manifest Generation

By default this is ran automatically by Step 2.

* Scans the entire archive
* Outputs `manifest.txt`
* Used only to prevent duplicate downloads

If a failure occurs in Steps 1 - 3, these steps can be reran out of order and they work fine granted the "rules" are followed.

---

### Step 4: Sort (Manual)

Move each `<video_id>` folder into a category:

```text
yt-dlp/1_New_Downloads/<video_id> → yt-dlp/<category_name>/<video_id>
```

Each video must exist in exactly one category (to prevent gui browser duplicates).

---

### Step 5: Catalog Generation (Manual)

Produces a machine-readable catalog.

Note: You have to redo this step after you download more videos, if you want the new videos to appear in the GUI browser (next step).

```bash
python3 5_generate_catalog.py
```

* Outputs `catalog.json`
* Required for GUI browser
* Supports `.mp4`, `.webm`, `.mkv`, videos and `.jpg`, `.jpeg` thumbnails

---

### Step 6: Browse

Browsing is handled by external software such as **[Visorum GUI](https://github.com/Ellie905/Visorum-gui)**.
More details below.

---

## Repair & Backfill Tools

Located in:

```
yt-dlp/1_New_Downloads/repair_tools/
```

These tools are **never run automatically** and exist only for maintenance or migration.

Some tools may contain absolute paths and require manual editing.

Use at your own risk.

---

## Platform Notes

### Linux

Fully supported.

### Windows

* Use WSL or Git Bash
* `yt-dlp.exe` is supported

### macOS

Behavior should mirror Linux.

---

## yt-dlp Versioning

Tested against:

```
yt-dlp 2025.10.22-1 - yt-dlp 2025.12.08-1
```

Future releases may change output formats.

**Recommended practice:**

* Test 1–2 videos before large batch runs
* Pin a known-good binary if breakage occurs

---

## Pre-built Binary

A pre-built Visorum GUI binary/appimage is included with the tools inside `1_New_Downloads/`.

- Built on Ubuntu 22.04
- Provided for convenience
- Does not require Python, pip, or a virtual environment

If the binary runs on your system, no build step is required.

If it does not run (e.g. due to libc or system compatibility),
use the provided source archive and follow the included build instructions.

Here is a [link](https://github.com/Ellie905/Visorum-gui) to the github repo for the GUI browser which also has the build instructions.

---

## Final Notes

* Designed for long-term preservation
* Consistency is prioritized over convenience
* The archive remains portable if structure rules are respected

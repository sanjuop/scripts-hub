# Scripts Hub — User Guide & Documentation

Welcome to **Scripts Hub**, a desktop interface built with **Qt (PySide6)** to manage, execute, and monitor all automation, media processing, and disk utility scripts in `D:\Scripts`.

---

## Table of Contents
1. [Quick Start](#1-quick-start)
2. [Interface Overview](#2-interface-overview)
3. [Parallel Script Execution](#3-parallel-script-execution)
4. [Managing Scripts & Optimizations](#4-managing-scripts--optimizations)
   - [Self Timer (Keep-Alive)](#self-timer-keep-alive-self_timerpy)
   - [Whisper Transcriber](#whisper-transcriber-ffmpegpy)
   - [Video Compressor](#video-compressor-video_compressorpy)
   - [Video Duration Calculator](#video-duration-calculator-video_durationpy)
   - [File Size & Codec Inspector](#file-size--codec-inspector-filesizepy)
   - [Hard Disk Replica](#hard-disk-replica-hard_disk_replicapy)
   - [Directory Inventory](#directory-inventory-directory_inventorypy)
5. [Automatic Windows Startup & System Tray](#5-automatic-windows-startup--system-tray)
6. [How to Add New Scripts Later](#6-how-to-add-new-scripts-later)
7. [Original Backups](#7-original-backups)

---

## 1. Quick Start

### How to Open Scripts Hub
* **Method 1 (Desktop Shortcut)**: Double-click the **`ScriptsHub`** shortcut directly on your Windows Desktop (featuring the electric blue icon ⚡).
* **Method 2 (From Folder)**: Double-click [**`D:\Scripts\launcher_app.pyw`**](file:///d:/Scripts/launcher_app.pyw).
* **Method 3 (Command Line)**:
  ```powershell
  cd D:\Scripts
  python launcher_app.pyw
  ```

---

## 2. Interface Overview

```
+---------------------------------------------------------------------------------------------+
| ⚡ SCRIPTS HUB          [ 2 Active Tasks ]                     [ ⏹ Stop All Tasks ]        |
+------------------------------+--------------------------------------------------------------+
| 🔍 Search scripts...         | Video Compressor                                             |
| Category: [ All Scripts ▼ ]  | Batch compress tutorial videos to HEVC (H.265)...            |
|                              | Status: READY   | 🐍 Python 3.12   | [✓ ffmpeg] [✓ ffprobe]  |
| 🟢 Self Timer (Keep-Alive)   +--------------------------------------------------------------+
| ⚪ Whisper Transcriber       | [ ▶ Run Script ]   [ ⏹ Stop ]   [ 📝 Edit Script ]           |
| 🟢 Video Compressor          +--------------------------------------------------------------+
| ⚪ Video Duration Calculator | Course Video Folder: [ D:\Courses\Python...        ] [Browse]|
| ⚪ File Size & Inspector     | 4K Handling:         [ 1080p ▼ ]                             |
| ⚪ Hard Disk Replica         | CRF Quality:         [ 28 ]                                  |
| ⚪ Directory Inventory       +--------------------------------------------------------------+
|                              | Terminal Output                               [Clear] [Copy] |
|                              | [ Tab: ▶ Video Compressor ]  [ Tab: 🟢 Self Timer ]          |
|                              | ------------------------------------------------------------ |
|                              | [20:15:02] [ffmpeg] frame=1420 fps=65 size=48MB time=00:02:14|
|                              |                                                              |
|                              | > Send Input: [                                 ] [Send]     |
+------------------------------+--------------------------------------------------------------+
| [+ Add Script]   [📁 Folder] | [☑ Launch on Windows Startup]  [☑ Minimize to Tray] | Ready  |
+------------------------------+--------------------------------------------------------------+
```

* **Sidebar**: Instant search and category filtering (**Media & Video**, **Disk & Backup**, **Automation & Keep-Awake**). Status dots reflect real-time execution:
  * 🟢 **Green**: Currently running
  * ⚪ **White/Gray**: Ready to run
  * 🔴 **Red**: Last run ended in an error
* **Center Detail Card**: Displays script metadata, dependency health (`ffmpeg`, `ffprobe`, `whisper`), and dynamic configuration options.
* **Terminal Tabs**: Displays real-time stdout and stderr output for each running script with timestamped logs.
* **Interactive Stdin**: An input bar beneath the logs allows replying to any interactive script prompts (`input()`) without opening a terminal.

---

## 3. Parallel Script Execution

Scripts Hub supports **true concurrent execution**:
* **Run Multiple Tasks Simultaneously**: You can start **Self Timer** to keep your computer awake, and simultaneously launch a **Video Compression** or **Whisper Transcription** job.
* **Independent Controls**: Each script has its own **`[ ▶ Run Script ]`** and **`[ ⏹ Stop ]`** buttons. Stopping one job will never affect other running tasks.
* **Global Stop**: Click **`[ ⏹ Stop All Tasks ]`** in the top bar or system tray to terminate all background scripts instantly.
* **Process Tree Termination**: On Windows, stopping a task automatically kills the entire process tree (including any spawned child processes like `ffmpeg.exe` or `whisper.exe`), ensuring no orphaned processes consume system resources.

---

## 4. Managing Scripts & Optimizations

All original scripts have been enhanced to be safe, fast, and configurable from both the UI and the command line.

### Self Timer (Keep-Alive) (`self_timer.py`)
* **Previous Issue**: Infinite `while True:` loop caused **100% CPU core utilization** and heat.
* **Optimization & Movement Modes**:
  * **0% CPU Overhead**: Replaced busy-wait with an efficient 1-second sleep loop.
  * **Immediate First Pulse**: Moves the cursor as soon as you hit **Run** so you have immediate visual confirmation.
  * **Three Modes**:
    1. **`random` (Default)**: Visibly moves the cursor across the screen to random coordinates (matches your original behavior).
    2. **`wiggle`**: Visibly slides the cursor back and forth 50px around its current position.
    3. **`stealth`**: Windows API keep-awake only (no mouse movement).
  * **Configurable**: Set pulse interval (default: 30s), duration in minutes, or a specific stop time (e.g. `22:00:00`).

### Whisper Transcriber (`ffmpeg.py`)
* **Features in UI**:
  * **Output Formats**: Select any combination of checkboxes: `JSON (word timestamps)`, `SRT (subtitles)`, `TXT`, `VTT`.
  * **Model Selector**: Choose between `tiny`, `base`, `small`, `medium`, `large-v3`, or `turbo`.
  * **Task & Language**: Choose `Transcribe` or `Translate to English`, and set target audio language.
  * **Skip Existing**: Automatically skips files that already have valid transcripts.
  * **Recursive Subfolder Scanning**: Check `Scan All Subfolders Recursively` to automatically index and transcribe all nested folders (e.g., course chapters/modules) in a single run. Saves transcripts right next to each video in its respective subfolder.
  * **Atomic Integrity & Resume Check**: Skips completed valid transcripts. Automatically detects and purges broken or 0-byte transcripts from interrupted runs so no files are skipped by mistake.
  * **Auto PC Shutdown**: Check `Shutdown PC when finished` to safely power off the computer when the entire batch completes (with a 60-second warning countdown and `shutdown /a` abort option).
  * **Advanced Flags**: Text field to pass any custom Whisper CLI flags (e.g. `--device cuda`).
* **How to Update Later**:
  * Click **`[ 📝 Edit Script ]`** in the UI to open `ffmpeg.py` in your code editor.
  * All arguments are handled cleanly using `argparse`.

### Video Compressor (`video_compressor.py`)
* **Features in UI**:
  * Select any course/tutorial folder using the visual **Browse** button.
  * Choose 4K handling: downscale to **1080p** or keep original resolution.
  * Adjust CRF quality (default: `28`) and speed preset (`fast`, `medium`, `slow`).
  * Non-interactive execution: bypasses terminal confirmation prompts automatically.
  * Generates an extensive side-by-side CSV compression report.
  * **Safe Interruption & Resume**:
    * Encodes to a `.part.mp4` temporary file first; only verified, completed videos are renamed to `.mp4`.
    * If the laptop shuts down or the script is stopped, any incomplete file is detected via duration verification, removed, and re-encoded cleanly from scratch on the next run.

### Video Duration Calculator (`video_duration.py`)
* **Features in UI**:
  * Select any folder containing videos.
  * Uses `ffprobe` to compute per-video playback lengths and cumulative total watch time (Hours, Minutes, Seconds).
  * **Silent Background Execution**: Runs with `CREATE_NO_WINDOW`, suppressing any flashing black terminal boxes completely.

### File Size & Codec Inspector (`fileSize.py`)
* **Features in UI**:
  * Inspects video files recursively.
  * Extracts video codecs, profiles, bitrates, dimensions, frame rates, audio codecs, sample rates, and channel layouts into `video_inventory.csv`.
  * Real-time progress logging (`[12/80] Inspecting: Lesson_01.mp4`).

### Hard Disk Replica (`Hard_disk_replica.py`)
* **Features in UI**:
  * Select source hard drive and replica target folder.
  * **Dry-Run Mode**: Check the `Dry Run` box to preview which files and folders will be added or removed without touching your drive!
  * **Safety Protection**: Enforces strict read-only access on the source drive.

### Directory Inventory (`directory_inventory.py`)
* **Features in UI**:
  * Indexes all files in a folder recursively into a plain text file.
  * Displays total file count and total folder size in MB/GB.

### Web Listing Scraper (`psdly.py`)
* **Features in UI**:
  * **Target Website URL**: Scrapes any PSDLY category or other website catalog (e.g. `https://www.psdly.site/ai-courses/`, `https://www.psdly.site/tutorials/`).
  * **Output CSV Location**: Click **Browse...** to save the resulting CSV anywhere on your computer (Desktop, downloads, or external drive). Defaults to `D:\Scripts\scraped_listings.csv`.
  * **Deep Extraction Mode**: Check `Extract Deep Details` to fetch **Source URL** (official sales page, e.g. Udemy), **Publisher** / Author, **File Size** (e.g. `5.1 GB`), **Updated Date** (e.g. `October 14, 2026`), and the course **Description** into dedicated CSV columns.
  * **Max Pages Limit**: Scrape all pages (`0`) or limit to e.g. `1`, `5`, or `10` pages.
  * **Keyword Filter**: Optional text filter (e.g. `Blender`, `Python`) to only export items matching your keywords.
  * **Custom Selector**: Optional CSS selector override for non-standard websites (leave blank for automatic smart detection).
  * **Richer Metadata**: Exports `title`, `url`, `page_discovered`, and `scraped_at` timestamp with Excel-ready `utf-8-sig` encoding.

---

## 5. Automatic Windows Startup & System Tray

### Enabling Auto-Startup
1. In the bottom status bar of Scripts Hub, check:  
   **`☑ Launch on Windows Startup`**
2. That's it! Scripts Hub creates a shortcut in:  
   `%APPDATA%\Microsoft\Windows\Start Menu\Programs\Startup\ScriptsHub.lnk`
3. When Windows boots, Scripts Hub will start automatically in the background using `pythonw.exe`.

### System Tray Behavior
* **Minimize to Tray**: When the **`☑ Minimize to Tray`** box is checked, clicking the window close button **`[X]`** hides Scripts Hub to the Windows notification area (near the taskbar clock) instead of quitting.
* **Tray Menu**: Right-click the system tray icon to:
  * **Open Scripts Hub**
  * **Stop All Running Scripts**
  * **Exit** (safely shuts down all background processes and exits).

---

## 6. How to Add New Scripts Later

Scripts Hub is fully extensible. You can register any new script in **two simple ways**:

### Method A: Through the UI (Easiest)
1. Open Scripts Hub.
2. In the bottom-left sidebar, click **`+ Add Script`**.
3. Fill in:
   * **Display Name**: e.g. `Audio Extractor`
   * **Description**: e.g. `Extracts MP3 audio from MKV files`
   * **Category**: e.g. `Media & Video`
   * **Script File**: Click **Browse...** and select your `.py` script.
4. Click **OK**. The new script immediately appears in the sidebar and is ready to run!

### Method B: Via `scripts_manifest.json` (Advanced Parameters)
If your new script accepts command-line arguments and you want visual inputs (folder pickers, dropdowns, sliders):
1. Open `D:\Scripts\scripts_manifest.json`.
2. Add a new JSON block under `"scripts"`:
   ```json
   {
     "id": "my_new_script",
     "name": "My New Script",
     "category": "Media & Video",
     "description": "Does something cool with video files.",
     "script_file": "my_script.py",
     "interpreter": "auto",
     "dependencies": ["ffmpeg"],
     "parameters": [
       {
         "name": "target_folder",
         "flag": "--folder",
         "type": "directory",
         "label": "Input Folder",
         "default": "D:\\Videos"
       },
       {
         "name": "quality",
         "flag": "--quality",
         "type": "choice",
         "label": "Quality Level",
         "options": ["High", "Medium", "Low"],
         "default": "High"
       }
     ]
   }
   ```
3. Save the file. Scripts Hub will automatically render the folder picker and dropdown!

---

## 7. Original Backups

All 8 original scripts were preserved in their exact pre-modification state before any changes were made:
* **Backup Directory**: `D:\Scripts\backup_original\`
  * `directory_inventory.py`
  * `ffmpeg.py`
  * `fileSize.py`
  * `Hard_disk_replica.py`
  * `self_timer.py`
  * `video_compressor.py`
  * `video_duration.py`
  * `whisper_to_otio.py`

---

## 8. UTF-8 & Special Character Encoding Support

All scripts and the Scripts Hub process launcher are configured to use UTF-8 output streams (`PYTHONIOENCODING=utf-8` and `sys.stdout.reconfigure(encoding="utf-8", errors="replace")`). File paths, course titles, or disk filenames containing special characters, smart quotes, dashes, accents, or non-English characters will print cleanly to the terminal without causing `UnicodeEncodeError`.


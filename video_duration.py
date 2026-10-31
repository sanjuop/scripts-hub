"""
Video Duration Calculator (video_duration.py)
Calculates individual and total cumulative playback durations using FFprobe.

Features:
- Configurable folder path via CLI argument (--path)
- Fallback to default directory
- Per-video duration and total watch time summary
"""

import sys
import argparse
import subprocess
from pathlib import Path

# Default fallback directory
DEFAULT_VIDEO_DIR = Path(r"D:\Lighting\Tom Noske - Video Creator Academy - MP4")

# Common video formats
VIDEO_EXTENSIONS = {
    ".mp4", ".mov", ".mkv", ".avi", ".wmv",
    ".flv", ".webm", ".m4v", ".mpeg", ".mpg",
    ".mts", ".m2ts", ".ts", ".3gp"
}


def get_video_duration(video_path):
    """Return video duration in seconds using FFprobe."""
    try:
        extra_flags = {}
        if sys.platform == "win32":
            extra_flags["creationflags"] = subprocess.CREATE_NO_WINDOW

        result = subprocess.run(
            [
                "ffprobe",
                "-v", "error",
                "-show_entries", "format=duration",
                "-of", "default=noprint_wrappers=1:nokey=1",
                str(video_path)
            ],
            capture_output=True,
            text=True,
            check=True,
            **extra_flags
        )
        return float(result.stdout.strip())
    except (subprocess.CalledProcessError, ValueError, FileNotFoundError):
        return None


def format_duration(seconds):
    """Format seconds as HH:MM:SS."""
    seconds = int(round(seconds))
    hours, remainder = divmod(seconds, 3600)
    minutes, seconds = divmod(remainder, 60)
    return f"{hours:02}:{minutes:02}:{seconds:02}"


def parse_arguments():
    parser = argparse.ArgumentParser(description="Calculate total and per-video duration.")
    parser.add_argument(
        "--path", "-p",
        type=str,
        default=str(DEFAULT_VIDEO_DIR),
        help=f"Target directory to scan (default: {DEFAULT_VIDEO_DIR})"
    )
    return parser.parse_args()


def main():
    args = parse_arguments()
    video_dir = Path(args.path)

    print("=" * 80, flush=True)
    print(" VIDEO DURATION CALCULATOR", flush=True)
    print("=" * 80, flush=True)
    print(f" Directory: {video_dir}\n", flush=True)

    if not video_dir.exists() or not video_dir.is_dir():
        print(f"[Error] Directory not found: {video_dir}", file=sys.stderr, flush=True)
        sys.exit(1)

    videos = sorted(
        p for p in video_dir.rglob("*")
        if p.is_file() and p.suffix.lower() in VIDEO_EXTENSIONS
    )

    if not videos:
        print("[Info] No video files found in target directory.", flush=True)
        return

    print(f"Found {len(videos)} video files. Analyzing durations with ffprobe...\n", flush=True)

    total_seconds = 0.0
    successful_count = 0

    for idx, video in enumerate(videos, start=1):
        duration = get_video_duration(video)
        try:
            rel_path = video.relative_to(video_dir)
        except ValueError:
            rel_path = video.name

        if duration is not None:
            total_seconds += duration
            successful_count += 1
            print(f"[{idx}/{len(videos)}] {rel_path} -> {format_duration(duration)} ({duration / 3600:.2f} hrs)", flush=True)
        else:
            print(f"[{idx}/{len(videos)}] {rel_path} -> [ERROR READING DURATION]", file=sys.stderr, flush=True)

    print("\n" + "=" * 80, flush=True)
    print(" SUMMARY", flush=True)
    print("=" * 80, flush=True)
    print(f" Total Videos Found : {len(videos)}", flush=True)
    print(f" Videos Processed   : {successful_count}", flush=True)
    print(f" COMBINED DURATION  : {format_duration(total_seconds)}", flush=True)
    print(f" Total Hours        : {total_seconds / 3600:.2f} hours", flush=True)
    print(f" Total Minutes      : {total_seconds / 60:.2f} minutes", flush=True)
    print("=" * 80, flush=True)


if __name__ == "__main__":
    main()

"""
Video File Size & Technical Stream Inspector (fileSize.py)
Extracts detailed video stream codecs, bitrates, resolutions, and audio parameters into a CSV sheet.

Features:
- Configurable root directory via CLI argument (--path)
- Configurable output CSV location (--output)
- Live progress indicator for large directories
"""

import sys
import csv
import json
import argparse
import subprocess
from pathlib import Path

DEFAULT_ROOT = Path(r"D:\Filmmaking\Tomorrows Filmmakers-Vol-1-10")

VIDEO_EXTENSIONS = {
    ".mp4", ".mkv", ".mov", ".avi", ".m4v", ".webm"
}


def run_ffprobe(file_path):
    command = [
        "ffprobe",
        "-v", "quiet",
        "-print_format", "json",
        "-show_format",
        "-show_streams",
        str(file_path),
    ]

    result = subprocess.run(
        command,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
    )

    if result.returncode != 0:
        raise RuntimeError(result.stderr)

    return json.loads(result.stdout)


def bitrate_kbps(value):
    if not value:
        return ""
    try:
        return round(float(value) / 1000, 1)
    except (ValueError, TypeError):
        return ""


def fps_value(value):
    if not value:
        return ""
    try:
        numerator, denominator = value.split("/")
        return round(float(numerator) / float(denominator), 3)
    except Exception:
        return value


def parse_arguments():
    parser = argparse.ArgumentParser(description="Inspect video files and export technical CSV inventory.")
    parser.add_argument(
        "--path", "-p",
        type=str,
        default=str(DEFAULT_ROOT),
        help=f"Target directory to inspect (default: {DEFAULT_ROOT})"
    )
    parser.add_argument(
        "--output", "-o",
        type=str,
        default="",
        help="Destination path for CSV report (default: <path>/video_inventory.csv)"
    )
    return parser.parse_args()


def main():
    args = parse_arguments()
    root_dir = Path(args.path)

    print("=" * 80, flush=True)
    print(" VIDEO STREAM & FILE SIZE INSPECTOR", flush=True)
    print("=" * 80, flush=True)
    print(f" Root Directory : {root_dir}", flush=True)

    if not root_dir.exists() or not root_dir.is_dir():
        print(f"[Error] Directory not found: {root_dir}", file=sys.stderr, flush=True)
        sys.exit(1)

    output_csv = Path(args.output) if args.output else root_dir / "video_inventory.csv"
    print(f" Output CSV     : {output_csv}\n", flush=True)

    files_to_scan = [
        f for f in root_dir.rglob("*")
        if f.is_file() and f.suffix.lower() in VIDEO_EXTENSIONS
    ]
    files_to_scan.sort()

    if not files_to_scan:
        print("[Info] No matching video files found.", flush=True)
        return

    print(f"Found {len(files_to_scan)} video files. Extracting stream metadata...\n", flush=True)

    videos = []

    for idx, file_path in enumerate(files_to_scan, start=1):
        try:
            rel_path = file_path.relative_to(root_dir)
        except ValueError:
            rel_path = file_path.name

        print(f"[{idx}/{len(files_to_scan)}] Inspecting: {rel_path}", flush=True)

        try:
            data = run_ffprobe(file_path)
            streams = data.get("streams", [])
            video_streams = [s for s in streams if s.get("codec_type") == "video"]
            audio_streams = [s for s in streams if s.get("codec_type") == "audio"]

            video = video_streams[0] if video_streams else {}
            audio = audio_streams[0] if audio_streams else {}
            format_info = data.get("format", {})
            size_bytes = file_path.stat().st_size

            row = {
                "File Name": file_path.name,
                "Relative Path": str(rel_path),
                "Size GB": round(size_bytes / (1024 ** 3), 3),
                "Size MB": round(size_bytes / (1024 ** 2), 1),
                "Duration Seconds": round(float(format_info.get("duration", 0) or 0), 2),
                "Duration Minutes": round(float(format_info.get("duration", 0) or 0) / 60, 2),
                "Container": format_info.get("format_name", ""),
                "Video Codec": video.get("codec_name", ""),
                "Video Profile": video.get("profile", ""),
                "Width": video.get("width", ""),
                "Height": video.get("height", ""),
                "FPS": fps_value(video.get("r_frame_rate", "")),
                "Pixel Format": video.get("pix_fmt", ""),
                "Video Bitrate Kbps": bitrate_kbps(video.get("bit_rate")),
                "Video Frames": video.get("nb_frames", ""),
                "Audio Codec": audio.get("codec_name", ""),
                "Audio Profile": audio.get("profile", ""),
                "Audio Bitrate Kbps": bitrate_kbps(audio.get("bit_rate")),
                "Audio Sample Rate": audio.get("sample_rate", ""),
                "Audio Channels": audio.get("channels", ""),
                "Audio Channel Layout": audio.get("channel_layout", ""),
                "Video Stream Count": len(video_streams),
                "Audio Stream Count": len(audio_streams),
                "Total Stream Count": len(streams),
            }
            videos.append(row)
        except Exception as error:
            print(f"  [ERROR] {file_path.name}: {error}", file=sys.stderr, flush=True)

    if videos:
        output_csv.parent.mkdir(parents=True, exist_ok=True)
        fieldnames = list(videos[0].keys())
        with open(output_csv, "w", newline="", encoding="utf-8-sig") as csv_file:
            writer = csv.DictWriter(csv_file, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(videos)

    print("\n" + "=" * 80, flush=True)
    print(" SCAN COMPLETED", flush=True)
    print(f" Total Videos Processed : {len(videos)}", flush=True)
    print(f" CSV Report Saved       : {output_csv}", flush=True)
    print("=" * 80, flush=True)


if __name__ == "__main__":
    main()

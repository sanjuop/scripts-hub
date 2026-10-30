import csv
import json
import subprocess
from pathlib import Path


ROOT = Path(r"D:\Filmmaking\Tomorrows Filmmakers-Vol-1-10")
OUTPUT = ROOT / "video_inventory.csv"

VIDEO_EXTENSIONS = {
    ".mp4",
    ".mkv",
    ".mov",
    ".avi",
    ".m4v",
    ".webm",
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


videos = []

for file_path in ROOT.rglob("*"):

    if not file_path.is_file():
        continue

    if file_path.suffix.lower() not in VIDEO_EXTENSIONS:
        continue

    print(f"Inspecting: {file_path}")

    try:
        data = run_ffprobe(file_path)

        streams = data.get("streams", [])

        video_streams = [
            s for s in streams
            if s.get("codec_type") == "video"
        ]

        audio_streams = [
            s for s in streams
            if s.get("codec_type") == "audio"
        ]

        video = video_streams[0] if video_streams else {}
        audio = audio_streams[0] if audio_streams else {}
        format_info = data.get("format", {})

        size_bytes = file_path.stat().st_size

        row = {
            "File Name": file_path.name,
            "Relative Path": str(file_path.relative_to(ROOT)),
            "Size GB": round(size_bytes / (1024 ** 3), 3),
            "Size MB": round(size_bytes / (1024 ** 2), 1),

            "Duration Seconds": round(
                float(format_info.get("duration", 0)), 2
            ),

            "Duration Minutes": round(
                float(format_info.get("duration", 0)) / 60, 2
            ),

            "Container": format_info.get("format_name", ""),

            "Video Codec": video.get("codec_name", ""),
            "Video Profile": video.get("profile", ""),

            "Width": video.get("width", ""),
            "Height": video.get("height", ""),

            "FPS": fps_value(
                video.get("r_frame_rate", "")
            ),

            "Pixel Format": video.get("pix_fmt", ""),

            "Video Bitrate Kbps": bitrate_kbps(
                video.get("bit_rate")
            ),

            "Video Frames": video.get("nb_frames", ""),

            "Audio Codec": audio.get("codec_name", ""),
            "Audio Profile": audio.get("profile", ""),

            "Audio Bitrate Kbps": bitrate_kbps(
                audio.get("bit_rate")
            ),

            "Audio Sample Rate": audio.get(
                "sample_rate", ""
            ),

            "Audio Channels": audio.get(
                "channels", ""
            ),

            "Audio Channel Layout": audio.get(
                "channel_layout", ""
            ),

            "Video Stream Count": len(video_streams),
            "Audio Stream Count": len(audio_streams),

            "Total Stream Count": len(streams),
        }

        videos.append(row)

    except Exception as error:
        print(f"ERROR: {file_path}")
        print(error)


if videos:

    fieldnames = list(videos[0].keys())

    with open(
        OUTPUT,
        "w",
        newline="",
        encoding="utf-8-sig",
    ) as csv_file:

        writer = csv.DictWriter(
            csv_file,
            fieldnames=fieldnames,
        )

        writer.writeheader()
        writer.writerows(videos)


print()
print("=" * 60)
print(f"Videos found : {len(videos)}")
print(f"CSV created  : {OUTPUT}")
print("=" * 60)
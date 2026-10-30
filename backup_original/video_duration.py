
import subprocess
from pathlib import Path

# Change this to your video directory
VIDEO_DIR = Path(r"D:\Lighting\Tom Noske - Video Creator Academy - MP4")

# Common video formats
VIDEO_EXTENSIONS = {
    ".mp4", ".mov", ".mkv", ".avi", ".wmv",
    ".flv", ".webm", ".m4v", ".mpeg", ".mpg",
    ".mts", ".m2ts", ".ts", ".3gp"
}


def get_video_duration(video_path):
    """Return video duration in seconds using FFprobe."""
    try:
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
            check=True
        )
        return float(result.stdout.strip())

    except (subprocess.CalledProcessError, ValueError, FileNotFoundError):
        print(f"  ERROR: Could not read duration")
        return None


def format_duration(seconds):
    """Format seconds as HH:MM:SS."""
    seconds = int(round(seconds))
    hours, remainder = divmod(seconds, 3600)
    minutes, seconds = divmod(remainder, 60)
    return f"{hours:02}:{minutes:02}:{seconds:02}"


def main():
    if not VIDEO_DIR.is_dir():
        print(f"Directory not found: {VIDEO_DIR}")
        return

    # Include videos in all subdirectories
    videos = sorted(
        p for p in VIDEO_DIR.rglob("*")
        if p.is_file() and p.suffix.lower() in VIDEO_EXTENSIONS
    )

    if not videos:
        print("No video files found.")
        return

    total_seconds = 0
    successful_count = 0

    print(f"\nVideo directory: {VIDEO_DIR}")
    print("=" * 90)

    for video in videos:
        duration = get_video_duration(video)

        if duration is not None:
            total_seconds += duration
            successful_count += 1

            print(
                f"{video.relative_to(VIDEO_DIR)}\n"
                f"    Duration: {format_duration(duration)}"
                f" ({duration / 3600:.2f} hours)"
            )

    print("=" * 90)
    print(f"Videos found:          {len(videos)}")
    print(f"Videos read:           {successful_count}")
    print(f"COMBINED DURATION:     {format_duration(total_seconds)}")
    print(f"Total hours:           {total_seconds / 3600:.2f}")
    print(f"Total minutes:         {total_seconds / 60:.2f}")


if __name__ == "__main__":
    main()
    
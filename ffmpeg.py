"""
Whisper Batch Transcriber & Audio/Video Tool (ffmpeg.py)
Transcribes video/audio files in a directory using OpenAI Whisper.

Features:
- Configurable output formats (JSON with word timestamps, SRT, TXT, VTT, TSV)
- Selectable Whisper model (tiny, base, small, medium, large-v3, turbo)
- Selectable language and task (transcribe vs translate)
- Skip already transcribed files
- Real-time progress output
"""

import os
import sys
import argparse
import subprocess
from pathlib import Path

# Supported video & audio extensions
MEDIA_EXTENSIONS = {
    ".mp4", ".mkv", ".mov", ".avi", ".flv", ".wmv", ".webm", ".ts",
    ".mp3", ".wav", ".m4a", ".aac", ".flac", ".ogg"
}

DEFAULT_FOLDER = r"D:\Lighting\Tom_Noske_Video_Creator Academy_MP4\3_Mastering_Scene_Creation_[Practical_Lessons]"


def parse_arguments():
    parser = argparse.ArgumentParser(
        description="Batch transcribe media files using OpenAI Whisper."
    )
    parser.add_argument(
        "--dir", "-d",
        type=str,
        default=DEFAULT_FOLDER,
        help=f"Target directory containing media files (default: {DEFAULT_FOLDER})"
    )
    parser.add_argument(
        "--output-dir", "-o",
        type=str,
        default="",
        help="Optional destination directory for transcripts (default: same as video file)"
    )
    parser.add_argument(
        "--formats", "-f",
        nargs="+",
        default=["json"],
        help="Output format(s): json, srt, txt, vtt, tsv (default: json)"
    )
    parser.add_argument(
        "--model", "-m",
        type=str,
        default="tiny",
        choices=["tiny", "tiny.en", "base", "base.en", "small", "small.en", "medium", "medium.en", "large", "large-v3", "turbo"],
        help="Whisper model size (default: tiny)"
    )
    parser.add_argument(
        "--language", "-l",
        type=str,
        default="English",
        help="Audio language (e.g., English, Russian, auto) (default: English)"
    )
    parser.add_argument(
        "--task",
        type=str,
        default="transcribe",
        choices=["transcribe", "translate"],
        help="Task: transcribe in original language or translate to English (default: transcribe)"
    )
    parser.add_argument(
        "--word-timestamps",
        action="store_true",
        default=True,
        help="Enable word-level timestamps (recommended for JSON / editing workflows)"
    )
    parser.add_argument(
        "--no-word-timestamps",
        action="store_false",
        dest="word_timestamps",
        help="Disable word-level timestamps"
    )
    parser.add_argument(
        "--skip-existing",
        action="store_true",
        default=True,
        help="Skip transcribing if target output format file already exists (default: True)"
    )
    parser.add_argument(
        "--overwrite",
        action="store_false",
        dest="skip_existing",
        help="Overwrite existing transcripts"
    )
    parser.add_argument(
        "--device",
        type=str,
        default="",
        help="Computation device: 'cuda', 'cpu', or leave empty for auto"
    )
    parser.add_argument(
        "--extra-args",
        type=str,
        default="",
        help="Additional raw arguments to pass directly to whisper CLI"
    )
    return parser.parse_args()


def find_whisper_executable():
    """Find whisper executable in PATH or standard python scripts folders."""
    # Check current environment
    import shutil
    whisper_path = shutil.which("whisper")
    if whisper_path:
        return whisper_path

    # Check known Python 3.14 Scripts folder where whisper is installed on this PC
    py314_whisper = Path(r"C:\Users\Sanjay D\AppData\Local\Programs\Python\Python314\Scripts\whisper.exe")
    if py314_whisper.exists():
        return str(py314_whisper)

    return "whisper"


def main():
    args = parse_arguments()
    target_dir = Path(args.dir)

    print("=" * 80, flush=True)
    print(" WHISPER BATCH TRANSCRIBER", flush=True)
    print("=" * 80, flush=True)
    print(f" Target Folder    : {target_dir}", flush=True)
    print(f" Model            : {args.model}", flush=True)
    print(f" Language         : {args.language}", flush=True)
    print(f" Task             : {args.task}", flush=True)
    print(f" Formats          : {', '.join(args.formats)}", flush=True)
    print(f" Word Timestamps  : {args.word_timestamps}", flush=True)
    print(f" Skip Existing    : {args.skip_existing}", flush=True)
    print("=" * 80, flush=True)

    if not target_dir.exists() or not target_dir.is_dir():
        print(f"\n[ERROR] Target folder does not exist: {target_dir}", file=sys.stderr, flush=True)
        sys.exit(1)

    whisper_exe = find_whisper_executable()

    # Find media files
    media_files = [
        f for f in target_dir.iterdir()
        if f.is_file() and f.suffix.lower() in MEDIA_EXTENSIONS and "downloads" not in f.name.lower()
    ]
    media_files.sort(key=lambda x: x.name.lower())

    if not media_files:
        print(f"\n[Info] No media files found in {target_dir}", flush=True)
        return

    print(f"\nFound {len(media_files)} media files to process.\n", flush=True)

    successful = 0
    skipped = 0
    failed = 0

    for idx, media_file in enumerate(media_files, start=1):
        out_folder = Path(args.output_dir) if args.output_dir else media_file.parent
        out_folder.mkdir(parents=True, exist_ok=True)

        # Check if already transcribed
        if args.skip_existing:
            all_exist = all(
                (out_folder / f"{media_file.stem}.{fmt}").exists()
                for fmt in args.formats
            )
            if all_exist:
                print(f"[{idx}/{len(media_files)}] Skipping {media_file.name} (Transcripts already exist)", flush=True)
                skipped += 1
                continue

        print(f"[{idx}/{len(media_files)}] Transcribing: {media_file.name}", flush=True)

        for fmt in args.formats:
            cmd = [
                whisper_exe,
                str(media_file),
                "--output_dir", str(out_folder),
                "--model", args.model,
                "--task", args.task,
                "--output_format", fmt
            ]

            if args.language.lower() != "auto":
                cmd.extend(["--language", args.language])

            if args.word_timestamps and fmt == "json":
                cmd.extend(["--word_timestamps", "True"])

            if args.device:
                cmd.extend(["--device", args.device])

            if args.extra_args:
                cmd.extend(args.extra_args.split())

            print(f"   Executing: {' '.join(cmd)}", flush=True)

            try:
                proc = subprocess.run(cmd, check=True)
                successful += 1
            except subprocess.CalledProcessError as e:
                print(f"   [Error] Whisper failed for {media_file.name}: {e}", file=sys.stderr, flush=True)
                failed += 1
            except FileNotFoundError:
                print(f"   [Error] Could not find whisper executable '{whisper_exe}'. Please verify your Whisper installation.", file=sys.stderr, flush=True)
                sys.exit(1)

        print("-" * 80, flush=True)

    print("\n" + "=" * 80, flush=True)
    print(" TRANSCRIPTION RUN COMPLETED", flush=True)
    print(f" Successful : {successful}", flush=True)
    print(f" Skipped    : {skipped}", flush=True)
    print(f" Failed     : {failed}", flush=True)
    print("=" * 80, flush=True)


if __name__ == "__main__":
    main()

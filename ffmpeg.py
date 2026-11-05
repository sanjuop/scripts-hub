"""
Whisper Batch Transcriber & Audio/Video Tool (ffmpeg.py)
Transcribes video/audio files in a directory using OpenAI Whisper.

Features:
- Recursive subfolder discovery (transcribes entire course folders effortlessly)
- Configurable output formats (JSON with word timestamps, SRT, TXT, VTT, TSV)
- Selectable Whisper model (tiny, base, small, medium, large-v3, turbo)
- Selectable language and task (transcribe vs translate)
- Atomic integrity check & auto-resume (detects and cleans up corrupted/0-byte transcripts)
- Optional PC shutdown when all transcriptions complete
- Real-time progress output
"""

import os
import sys
if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
        sys.stderr.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass
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
        help="Optional destination directory for transcripts (default: same folder as each video file)"
    )
    parser.add_argument(
        "--recursive", "-r",
        action="store_true",
        default=True,
        help="Scan target directory and all subdirectories recursively for media files (default: True)"
    )
    parser.add_argument(
        "--no-recursive",
        action="store_false",
        dest="recursive",
        help="Only scan the immediate directory, ignoring subdirectories"
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
        help="Skip transcribing if target output format file already exists & is valid (default: True)"
    )
    parser.add_argument(
        "--overwrite",
        action="store_false",
        dest="skip_existing",
        help="Overwrite existing transcripts"
    )
    parser.add_argument(
        "--shutdown",
        action="store_true",
        default=False,
        help="Automatically shut down the PC after all files finish transcribing (default: False)"
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
    import shutil
    whisper_path = shutil.which("whisper")
    if whisper_path:
        return whisper_path

    py314_whisper = Path(r"C:\Users\Sanjay D\AppData\Local\Programs\Python\Python314\Scripts\whisper.exe")
    if py314_whisper.exists():
        return str(py314_whisper)

    return "whisper"


def is_valid_transcript(file_path: Path, fmt: str) -> bool:
    """Check if file exists, is non-empty, and structurally valid."""
    if not file_path.exists():
        return False
    try:
        if file_path.stat().st_size == 0:
            return False
        if fmt == "json":
            import json
            with open(file_path, "r", encoding="utf-8") as f:
                data = json.load(f)
                if not data or ("text" not in data and "segments" not in data):
                    return False
        return True
    except Exception:
        return False


def main():
    args = parse_arguments()
    target_dir = Path(args.dir)

    print("=" * 80, flush=True)
    print(" WHISPER BATCH TRANSCRIBER", flush=True)
    print("=" * 80, flush=True)
    print(f" Target Folder    : {target_dir}", flush=True)
    print(f" Recursive Scan   : {args.recursive}", flush=True)
    print(f" Model            : {args.model}", flush=True)
    print(f" Language         : {args.language}", flush=True)
    print(f" Task             : {args.task}", flush=True)
    print(f" Formats          : {', '.join(args.formats)}", flush=True)
    print(f" Word Timestamps  : {args.word_timestamps}", flush=True)
    print(f" Skip Existing    : {args.skip_existing}", flush=True)
    print(f" Auto Shutdown PC : {args.shutdown}", flush=True)
    print("=" * 80, flush=True)

    if not target_dir.exists() or not target_dir.is_dir():
        print(f"\n[ERROR] Target folder does not exist: {target_dir}", file=sys.stderr, flush=True)
        sys.exit(1)

    whisper_exe = find_whisper_executable()

    # Discover media files (recursive or top-level)
    if args.recursive:
        media_files = [
            f for f in target_dir.rglob("*")
            if f.is_file() and f.suffix.lower() in MEDIA_EXTENSIONS and "downloads" not in f.name.lower()
        ]
    else:
        media_files = [
            f for f in target_dir.iterdir()
            if f.is_file() and f.suffix.lower() in MEDIA_EXTENSIONS and "downloads" not in f.name.lower()
        ]

    # Sort files cleanly by path so subfolders are processed in order
    media_files.sort(key=lambda x: str(x).lower())

    if not media_files:
        print(f"\n[Info] No media files found in {target_dir}", flush=True)
        return

    print(f"\nFound {len(media_files)} media files to process.\n", flush=True)

    successful = 0
    skipped = 0
    failed = 0

    for idx, media_file in enumerate(media_files, start=1):
        rel_display = media_file.relative_to(target_dir) if args.recursive else media_file.name
        out_folder = Path(args.output_dir) if args.output_dir else media_file.parent
        out_folder.mkdir(parents=True, exist_ok=True)

        # Integrity check: clean up any 0-byte or corrupted transcripts from a prior interrupted run
        for fmt in args.formats:
            transcript_path = out_folder / f"{media_file.stem}.{fmt}"
            if transcript_path.exists() and not is_valid_transcript(transcript_path, fmt):
                print(f"   [Notice] Cleaning broken/incomplete transcript from previous interrupted run: {transcript_path.name}", flush=True)
                try:
                    transcript_path.unlink()
                except Exception:
                    pass

        # Check if already transcribed
        if args.skip_existing:
            all_exist = all(
                is_valid_transcript(out_folder / f"{media_file.stem}.{fmt}", fmt)
                for fmt in args.formats
            )
            if all_exist:
                print(f"[{idx}/{len(media_files)}] Skipping {rel_display} (Transcripts already exist & valid)", flush=True)
                skipped += 1
                continue

        formats_to_run = [
            fmt for fmt in args.formats
            if not is_valid_transcript(out_folder / f"{media_file.stem}.{fmt}", fmt)
        ]

        print(f"[{idx}/{len(media_files)}] Transcribing: {rel_display}", flush=True)

        file_has_error = False
        for fmt in formats_to_run:
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
                extra_flags = {"creationflags": subprocess.CREATE_NO_WINDOW} if sys.platform == "win32" else {}
                subprocess.run(cmd, check=True, **extra_flags)
            except subprocess.CalledProcessError as e:
                print(f"   [Error] Whisper failed for {media_file.name} ({fmt}): {e}", file=sys.stderr, flush=True)
                file_has_error = True
            except FileNotFoundError:
                print(f"   [Error] Could not find whisper executable '{whisper_exe}'. Please verify your Whisper installation.", file=sys.stderr, flush=True)
                sys.exit(1)

        if file_has_error:
            failed += 1
        else:
            successful += 1

        print("-" * 80, flush=True)

    print("\n" + "=" * 80, flush=True)
    print(" TRANSCRIPTION RUN COMPLETED", flush=True)
    print(f" Successful : {successful}", flush=True)
    print(f" Skipped    : {skipped}", flush=True)
    print(f" Failed     : {failed}", flush=True)
    print("=" * 80, flush=True)

    # Automatic PC Shutdown if requested
    if args.shutdown:
        print("\n" + "!" * 80, flush=True)
        print(" [SHUTDOWN] All transcription tasks have finished successfully.", flush=True)
        print(" [SHUTDOWN] System will shut down in 60 seconds...", flush=True)
        print(" [SHUTDOWN] To abort shutdown, open Run (Win+R) or Command Prompt and type: shutdown /a", flush=True)
        print("!" * 80 + "\n", flush=True)

        if sys.platform == "win32":
            try:
                subprocess.run(["shutdown", "/s", "/t", "60", "/c", "Whisper Transcription Complete. Shutting down system."])
            except Exception as e:
                print(f"[Error] Failed to initiate shutdown: {e}", file=sys.stderr, flush=True)
        else:
            try:
                subprocess.run(["shutdown", "-h", "+1"])
            except Exception as e:
                print(f"[Error] Failed to initiate shutdown: {e}", file=sys.stderr, flush=True)


if __name__ == "__main__":
    main()

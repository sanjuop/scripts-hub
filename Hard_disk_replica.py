"""
Hard Disk Replica Generator (Hard_disk_replica.py)
Creates a lightweight shadow copy of an external hard drive with small text placeholder files.
Allows browsing and indexing contents offline without needing the physical drive plugged in.

Features:
- Configurable source and replica locations (--source, --replica)
- Non-interactive mode (--yes) for automated and GUI execution
- Safe dry-run mode (--dry-run) to preview additions and deletions
- Strict safety verification (source is strictly read-only)
"""

import os
import sys
import argparse
from pathlib import Path

DEFAULT_SOURCE = Path(r"E:\Toolkit\Backup\SANJUOP\D")
DEFAULT_REPLICA = Path(r"G:\My Drive\HardDisk_Replica")


def safety_check(source, replica, non_interactive=False):
    s = source.resolve()
    r = replica.resolve()

    print("=" * 70, flush=True)
    print(" HARD DISK REPLICA SAFETY CHECK", flush=True)
    print("=" * 70, flush=True)
    print(f" SOURCE HARD DISK : {s}", flush=True)
    print(f" REPLICA FOLDER   : {r}", flush=True)
    print("\nIMPORTANT:", flush=True)
    print(" The source disk is strictly READ-ONLY. Nothing will be modified on source.", flush=True)
    print(" Only the REPLICA directory will be created, updated, or synchronized.", flush=True)

    if s == r:
        print("\n[ERROR] Source and replica are the exact same location. Aborting.", file=sys.stderr, flush=True)
        return False

    try:
        r.relative_to(s)
        print("\n[ERROR] Replica is located inside the source drive. Aborting.", file=sys.stderr, flush=True)
        return False
    except ValueError:
        pass

    if non_interactive:
        print("\n[Auto-Confirmed] Non-interactive mode enabled (--yes). Proceeding.\n", flush=True)
        return True

    try:
        answer = input("\nContinue synchronization? [Y/N]: ").strip().lower()
        return answer == "y"
    except EOFError:
        return True


def scan_source(source_dir):
    folders = set()
    files = set()
    print(f"Scanning source: {source_dir}...", flush=True)
    for root, dirs, filenames in os.walk(source_dir):
        root_path = Path(root)
        for directory in dirs:
            folder_path = root_path / directory
            try:
                folders.add(folder_path.relative_to(source_dir))
            except ValueError:
                continue
        for filename in filenames:
            file_path = root_path / filename
            try:
                files.add(file_path.relative_to(source_dir))
            except ValueError:
                continue
    return folders, files


def replica_file_path(source_file):
    if source_file.suffix.lower() == ".txt":
        return source_file
    return Path(str(source_file) + ".txt")


def scan_replica(replica_dir):
    folders = set()
    files = set()
    if not replica_dir.exists():
        return folders, files
    for root, dirs, filenames in os.walk(replica_dir):
        root_path = Path(root)
        for directory in dirs:
            folder_path = root_path / directory
            try:
                folders.add(folder_path.relative_to(replica_dir))
            except ValueError:
                continue
        for filename in filenames:
            file_path = root_path / filename
            try:
                files.add(file_path.relative_to(replica_dir))
            except ValueError:
                continue
    return folders, files


def create_placeholder(source_file, replica_file, dry_run=False):
    if dry_run:
        return
    replica_file.parent.mkdir(parents=True, exist_ok=True)
    with open(replica_file, "w", encoding="utf-8") as f:
        f.write(f"Original file: {source_file.name}\n")
        f.write(f"Original path: {source_file}\n")


def parse_arguments():
    parser = argparse.ArgumentParser(description="Synchronize a lightweight text replica of a disk directory.")
    parser.add_argument(
        "--source", "-s",
        type=str,
        default=str(DEFAULT_SOURCE),
        help=f"Source hard disk directory to scan (default: {DEFAULT_SOURCE})"
    )
    parser.add_argument(
        "--replica", "-r",
        type=str,
        default=str(DEFAULT_REPLICA),
        help=f"Destination directory for replica placeholders (default: {DEFAULT_REPLICA})"
    )
    parser.add_argument(
        "--dry-run", "-n",
        action="store_true",
        help="Simulate the scan and changes without creating or deleting files"
    )
    parser.add_argument(
        "--yes", "-y",
        action="store_true",
        help="Bypass the interactive confirmation prompt"
    )
    return parser.parse_args()


def main():
    args = parse_arguments()
    source_dir = Path(args.source)
    replica_dir = Path(args.replica)

    if not safety_check(source_dir, replica_dir, non_interactive=args.yes):
        print("\n[Cancelled] Operation aborted by user.", flush=True)
        return

    if not source_dir.exists():
        print(f"\n[ERROR] Source hard drive does not exist or is disconnected: {source_dir}", file=sys.stderr, flush=True)
        sys.exit(1)

    if not source_dir.is_dir():
        print(f"\n[ERROR] Source is not a directory: {source_dir}", file=sys.stderr, flush=True)
        sys.exit(1)

    if args.dry_run:
        print("[DRY RUN MODE] No disk changes will be made.\n", flush=True)
    else:
        replica_dir.mkdir(parents=True, exist_ok=True)

    source_folders, source_files = scan_source(source_dir)
    print(f"Source scan complete: {len(source_folders)} folders, {len(source_files)} files.\n", flush=True)

    expected_folders = set(source_folders)
    expected_files = {replica_file_path(f) for f in source_files}

    replica_folders, replica_files = scan_replica(replica_dir)

    folders_added = 0
    for folder in sorted(expected_folders):
        dest = replica_dir / folder
        if not dest.exists():
            if not args.dry_run:
                dest.mkdir(parents=True, exist_ok=True)
            print(f"[FOLDER ADD]    {folder}", flush=True)
            folders_added += 1

    files_added = 0
    for source_file in sorted(source_files):
        exp_file = replica_file_path(source_file)
        dest = replica_dir / exp_file
        if not dest.exists():
            original = source_dir / source_file
            create_placeholder(original, dest, dry_run=args.dry_run)
            print(f"[FILE ADD]      {source_file}", flush=True)
            files_added += 1

    files_removed = 0
    for rep_file in sorted(replica_files):
        if rep_file not in expected_files:
            dest = replica_dir / rep_file
            if dest.is_file():
                if not args.dry_run:
                    try:
                        dest.unlink()
                    except OSError as e:
                        print(f"[FILE REMOVE ERROR] {rep_file}: {e}", file=sys.stderr, flush=True)
                        continue
                print(f"[FILE REMOVE]   {rep_file}", flush=True)
                files_removed += 1

    folders_removed = 0
    current_folders, _ = scan_replica(replica_dir)
    for folder in sorted(current_folders, key=lambda x: len(x.parts), reverse=True):
        if folder not in expected_folders:
            dest = replica_dir / folder
            try:
                if not any(dest.iterdir()):
                    if not args.dry_run:
                        dest.rmdir()
                    print(f"[FOLDER REMOVE] {folder}", flush=True)
                    folders_removed += 1
            except OSError:
                pass

    print("\n" + "=" * 70, flush=True)
    print(" SYNCHRONIZATION COMPLETE" + (" (DRY RUN)" if args.dry_run else ""), flush=True)
    print("=" * 70, flush=True)
    print(f" Folders added   : {folders_added}", flush=True)
    print(f" Folders removed : {folders_removed}", flush=True)
    print(f" Files added     : {files_added}", flush=True)
    print(f" Files removed   : {files_removed}", flush=True)
    print(f" Replica Path    : {replica_dir}", flush=True)
    print(" Source was not modified in any way.", flush=True)
    print("=" * 70, flush=True)


if __name__ == "__main__":
    main()

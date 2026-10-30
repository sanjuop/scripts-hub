"""
Directory Inventory Scanner (directory_inventory.py)
Scans a folder recursively and generates a plain text index of all file paths.

Features:
- Configurable source directory (--source)
- Configurable output file (--output)
- File count and summary statistics
"""

import sys
import argparse
from pathlib import Path

DEFAULT_SOURCE = Path(r"D:\Editing\film-editing-pro-the-art-of-drama-editing\Film Editing Pro - The Art Of Drama Editing\The Artor Drama Eiting PrO Dowloads\Footage")
DEFAULT_OUTPUT = DEFAULT_SOURCE / "file_inventory.txt"


def format_bytes(size):
    for unit in ["B", "KB", "MB", "GB", "TB"]:
        if size < 1024.0:
            return f"{size:.2f} {unit}"
        size /= 1024.0
    return f"{size:.2f} PB"


def parse_arguments():
    parser = argparse.ArgumentParser(description="Recursively index all files in a directory.")
    parser.add_argument(
        "--source", "-s",
        type=str,
        default=str(DEFAULT_SOURCE),
        help=f"Directory to scan (default: {DEFAULT_SOURCE})"
    )
    parser.add_argument(
        "--output", "-o",
        type=str,
        default="",
        help="Destination text file (default: <source>/file_inventory.txt)"
    )
    return parser.parse_args()


def main():
    args = parse_arguments()
    source_dir = Path(args.source)

    print("=" * 80, flush=True)
    print(" DIRECTORY INVENTORY SCANNER", flush=True)
    print("=" * 80, flush=True)
    print(f" Source Directory : {source_dir}", flush=True)

    if not source_dir.exists() or not source_dir.is_dir():
        print(f"[Error] Directory not found: {source_dir}", file=sys.stderr, flush=True)
        sys.exit(1)

    output_file = Path(args.output) if args.output else source_dir / "file_inventory.txt"
    print(f" Output File      : {output_file}\n", flush=True)

    print(f"Scanning '{source_dir.resolve()}'...", flush=True)

    file_paths = []
    total_size = 0

    for path in sorted(source_dir.rglob("*")):
        if path.is_file():
            file_paths.append(str(path.resolve()))
            try:
                total_size += path.stat().st_size
            except OSError:
                pass

    output_file.parent.mkdir(parents=True, exist_ok=True)
    with output_file.open("w", encoding="utf-8") as file:
        file.write(f"Directory inventory: {source_dir.resolve()}\n")
        file.write(f"Total files: {len(file_paths)}\n")
        file.write(f"Total size: {format_bytes(total_size)}\n")
        file.write("=" * 100 + "\n")
        for path in file_paths:
            file.write(path + "\n")

    print("\n" + "=" * 80, flush=True)
    print(" SCAN COMPLETED", flush=True)
    print(f" Total files found : {len(file_paths)}", flush=True)
    print(f" Total folder size : {format_bytes(total_size)}", flush=True)
    print(f" Output saved to   : {output_file.resolve()}", flush=True)
    print("=" * 80, flush=True)


if __name__ == "__main__":
    main()

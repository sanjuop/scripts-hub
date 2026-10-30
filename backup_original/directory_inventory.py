
from pathlib import Path

# Directory to scan
SOURCE_DIR = Path(r"D:\Editing\film-editing-pro-the-art-of-drama-editing\Film Editing Pro - The Art Of Drama Editing\The Artor Drama Eiting PrO Dowloads\Footage")

# Output text file
OUTPUT_FILE = Path(r"D:\Editing\film-editing-pro-the-art-of-drama-editing\Film Editing Pro - The Art Of Drama Editing\The Artor Drama Eiting PrO Dowloads\Footage\file_inventory.txt")


def main():
    if not SOURCE_DIR.is_dir():
        print(f"Directory not found: {SOURCE_DIR}")
        return

    file_paths = sorted(
        str(path.resolve())
        for path in SOURCE_DIR.rglob("*")
        if path.is_file()
    )

    with OUTPUT_FILE.open("w", encoding="utf-8") as file:
        file.write(f"Directory inventory: {SOURCE_DIR.resolve()}\n")
        file.write("=" * 100 + "\n")

        for path in file_paths:
            file.write(path + "\n")

    print(f"Scan completed: {SOURCE_DIR}")
    print(f"Total files found: {len(file_paths)}")
    print(f"Output saved to: {OUTPUT_FILE.resolve()}")


if __name__ == "__main__":
    main()

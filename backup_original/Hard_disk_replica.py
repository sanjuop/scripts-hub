import os
from pathlib import Path

# ============================================================
# CONFIGURATION
# ============================================================

# HARD DISK TO SCAN
# IMPORTANT: Change this to your hard disk drive.
SOURCE = Path(r"E:\Toolkit\Backup\SANJUOP\D")

# LOCAL FOLDER WHERE THE LIGHTWEIGHT REPLICA WILL BE CREATED
REPLICA = Path(r"G:\My Drive\HardDisk_Replica")


# ============================================================
# SAFETY CHECK
# ============================================================

def safety_check():

    source = SOURCE.resolve()
    replica = REPLICA.resolve()

    print("=" * 70)
    print("HARD DISK REPLICA")
    print("=" * 70)

    print(f"\nSOURCE HARD DISK : {source}")
    print(f"REPLICA           : {replica}")

    print("\nIMPORTANT:")
    print("The source hard disk will ONLY be read.")
    print("The script will NOT create, delete, rename,")
    print("move or modify anything on the source.")

    print("\nOnly the REPLICA folder will be modified.")

    if source == replica:
        print("\nERROR: Source and replica are the same location.")
        return False

    # Prevent replica from being inside source
    try:
        replica.relative_to(source)

        print("\nERROR: Replica is inside the source.")
        print("Please choose a replica location outside the hard disk.")

        return False

    except ValueError:
        pass

    answer = input("\nContinue? [Y/N]: ").strip().lower()

    return answer == "y"


# ============================================================
# SCAN SOURCE
# ============================================================

def scan_source():

    folders = set()
    files = set()

    print("\nScanning hard disk...")

    for root, dirs, filenames in os.walk(SOURCE):

        root_path = Path(root)

        # ----------------------------------------------------
        # FOLDERS
        # ----------------------------------------------------

        for directory in dirs:

            folder_path = root_path / directory

            try:
                relative_path = folder_path.relative_to(SOURCE)
                folders.add(relative_path)

            except ValueError:
                continue

        # ----------------------------------------------------
        # FILES
        # ----------------------------------------------------

        for filename in filenames:

            file_path = root_path / filename

            try:
                relative_path = file_path.relative_to(SOURCE)
                files.add(relative_path)

            except ValueError:
                continue

    return folders, files


# ============================================================
# CONVERT SOURCE FILE TO REPLICA FILE
# ============================================================

def replica_file_path(source_file):

    # Existing TXT files remain TXT
    if source_file.suffix.lower() == ".txt":
        return source_file

    # Everything else gets .txt appended
    return Path(str(source_file) + ".txt")


# ============================================================
# SCAN REPLICA
# ============================================================

def scan_replica():

    folders = set()
    files = set()

    if not REPLICA.exists():
        return folders, files

    for root, dirs, filenames in os.walk(REPLICA):

        root_path = Path(root)

        # ----------------------------------------------------
        # FOLDERS
        # ----------------------------------------------------

        for directory in dirs:

            folder_path = root_path / directory

            try:
                relative_path = folder_path.relative_to(REPLICA)
                folders.add(relative_path)

            except ValueError:
                continue

        # ----------------------------------------------------
        # FILES
        # ----------------------------------------------------

        for filename in filenames:

            file_path = root_path / filename

            try:
                relative_path = file_path.relative_to(REPLICA)
                files.add(relative_path)

            except ValueError:
                continue

    return folders, files


# ============================================================
# CREATE PLACEHOLDER
# ============================================================

def create_placeholder(source_file, replica_file):

    replica_file.parent.mkdir(
        parents=True,
        exist_ok=True
    )

    with open(replica_file, "w", encoding="utf-8") as f:

        f.write(f"Original file: {source_file.name}\n")
        f.write(f"Original path: {source_file}\n")


# ============================================================
# SYNCHRONIZE
# ============================================================

def synchronize():

    # --------------------------------------------------------
    # SAFETY
    # --------------------------------------------------------

    if not safety_check():
        print("\nOperation cancelled.")
        return

    # --------------------------------------------------------
    # CHECK SOURCE
    # --------------------------------------------------------

    if not SOURCE.exists():

        print("\nERROR:")
        print(f"Source does not exist: {SOURCE}")

        print("\nMake sure the hard disk is connected.")
        return

    if not SOURCE.is_dir():

        print("\nERROR:")
        print(f"Source is not a directory: {SOURCE}")

        return

    # --------------------------------------------------------
    # CREATE REPLICA ROOT
    # --------------------------------------------------------

    REPLICA.mkdir(
        parents=True,
        exist_ok=True
    )

    # --------------------------------------------------------
    # SCAN SOURCE
    # --------------------------------------------------------

    source_folders, source_files = scan_source()

    print("\nSource scan complete.")

    print(f"Folders found : {len(source_folders)}")
    print(f"Files found   : {len(source_files)}")

    # --------------------------------------------------------
    # BUILD EXPECTED REPLICA STRUCTURE
    # --------------------------------------------------------

    expected_folders = set(source_folders)
    expected_files = set()

    for source_file in source_files:

        replica_file = replica_file_path(source_file)

        expected_files.add(replica_file)

    # --------------------------------------------------------
    # SCAN EXISTING REPLICA
    # --------------------------------------------------------

    replica_folders, replica_files = scan_replica()

    # ========================================================
    # ADD MISSING FOLDERS
    # ========================================================

    folders_added = 0

    for folder in sorted(expected_folders):

        destination = REPLICA / folder

        if not destination.exists():

            destination.mkdir(
                parents=True,
                exist_ok=True
            )

            print(f"[FOLDER ADD]    {folder}")

            folders_added += 1

    # ========================================================
    # ADD MISSING FILES
    # ========================================================

    files_added = 0

    for source_file in sorted(source_files):

        expected_file = replica_file_path(source_file)

        destination = REPLICA / expected_file

        if not destination.exists():

            original = SOURCE / source_file

            create_placeholder(
                original,
                destination
            )

            print(f"[FILE ADD]       {source_file}")

            files_added += 1

    # ========================================================
    # REMOVE EXTRA FILES FROM REPLICA
    # ========================================================

    files_removed = 0

    for replica_file in sorted(replica_files):

        if replica_file not in expected_files:

            destination = REPLICA / replica_file

            if destination.is_file():

                destination.unlink()

                print(f"[FILE REMOVE]    {replica_file}")

                files_removed += 1

    # ========================================================
    # REMOVE EXTRA FOLDERS FROM REPLICA
    #
    # This is done AFTER removing files.
    #
    # Empty folders that actually exist on the hard disk
    # remain because they are present in expected_folders.
    # ========================================================

    folders_removed = 0

    # Re-scan replica after file deletion
    current_folders, _ = scan_replica()

    for folder in sorted(
        current_folders,
        key=lambda x: len(x.parts),
        reverse=True
    ):

        if folder not in expected_folders:

            destination = REPLICA / folder

            try:

                # Only remove if empty
                if not any(destination.iterdir()):

                    destination.rmdir()

                    print(f"[FOLDER REMOVE] {folder}")

                    folders_removed += 1

            except OSError:
                pass

    # ========================================================
    # SUMMARY
    # ========================================================

    print("\n")
    print("=" * 70)
    print("SYNCHRONIZATION COMPLETE")
    print("=" * 70)

    print(f"\nSource folders          : {len(source_folders)}")
    print(f"Source files            : {len(source_files)}")

    print("\nReplica changes:")

    print(f"Folders added           : {folders_added}")
    print(f"Folders removed         : {folders_removed}")

    print(f"Files added             : {files_added}")
    print(f"Files removed           : {files_removed}")

    print("\nSOURCE WAS NOT MODIFIED.")
    print(f"\nReplica location:")
    print(REPLICA)

    print("\nDone.")


# ============================================================
# MAIN
# ============================================================

if __name__ == "__main__":
    synchronize()
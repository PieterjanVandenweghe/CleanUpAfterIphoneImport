#!/usr/bin/env python3
"""
move_imported_files.py

Move files from a source directory into D:/Foto/<year>/<MM_monthname>
based on Date Taken (EXIF) or Date Modified.

Supports:
  --dry-run   : simulate moves without changing files
  --base PATH : set base target directory (default: D:/Foto)

Usage:
  python move_imported_files.py "D:\Foto\_ImportIphone\PJ" [--base D:\Foto] [--dry-run]

Requires:
  pip install Pillow
"""

import os
import sys
import shutil
import datetime
from pathlib import Path

try:
    from PIL import Image, ExifTags
except Exception:
    print("This script requires Pillow. Install with: pip install Pillow")
    sys.exit(1)


# Dutch month names with zero-padded month number prefix
DUTCH_MONTHS = [
    "01_januari", "02_februari", "03_maart", "04_april",
    "05_mei", "06_juni", "07_juli", "08_augustus",
    "09_september", "10_oktober", "11_november", "12_december"
]

# Allowed image and video file extensions (lowercase)
MEDIA_EXTENSIONS = {
    ".jpg", ".jpeg", ".tiff", ".tif", ".png", ".heic", ".heif",
    ".gif", ".bmp", ".webp",
    ".mp4", ".mov", ".avi", ".mkv", ".3gp", ".mts", ".m4v"
}


def get_exif_datetime_taken(path: Path):
    """Try to read EXIF DateTimeOriginal or DateTime; return datetime or None."""
    try:
        with Image.open(path) as img:
            exif = img._getexif()
            if not exif:
                return None
            exif_by_name = {ExifTags.TAGS.get(k, k): v for k, v in exif.items()}
            date_str = exif_by_name.get("DateTimeOriginal") or exif_by_name.get("DateTime")
            if not date_str:
                return None
            return datetime.datetime.strptime(date_str, "%Y:%m:%d %H:%M:%S")
    except Exception:
        return None


def get_file_datetime(path: Path):
    """Get Date Taken (EXIF) or fall back to modification time."""
    if path.suffix.lower() in {".jpg", ".jpeg", ".tiff", ".tif", ".png", ".heic", ".heif"}:
        dt = get_exif_datetime_taken(path)
        if dt:
            return dt
    return datetime.datetime.fromtimestamp(path.stat().st_mtime)


def month_folder_name(dt: datetime.datetime) -> str:
    """Return folder name like '10_oktober' for a given datetime."""
    return DUTCH_MONTHS[dt.month - 1]


def move_files(source_dir: str, base_target: str = "D:/Foto", dry_run=False):
    """Move or simulate moving files based on EXIF or modified date."""
    source = Path(source_dir)
    if not source.exists() or not source.is_dir():
        print(f"❌ Source directory not found: {source_dir}")
        return

    base_target = Path(base_target)
    conflicts, moved_count, skipped_aae, errors = [], 0, 0, []
    skipped_non_media = 0

    print(f"{'🔎 Simulating move' if dry_run else '🚚 Moving files'} from: {source}")
    print(f"Base target: {base_target}")
    print(f"Dry run mode: {'ON' if dry_run else 'OFF'}\n")

    for root, _, files in os.walk(source):
        for fname in files:
            ext = Path(fname).suffix.lower()

            if ext == ".aae":
                skipped_aae += 1
                continue

            # Only process known image/video file types
            if ext not in MEDIA_EXTENSIONS:
                skipped_non_media += 1
                continue

            src_path = Path(root) / fname

            try:
                dt = get_file_datetime(src_path)
                year = str(dt.year)
                month_folder = month_folder_name(dt)
                dest_dir = base_target / year / month_folder
                dest_dir.mkdir(parents=True, exist_ok=True)

                dest_path = dest_dir / fname

                if dest_path.exists():
                    conflicts.append({"source": str(src_path), "destination": str(dest_path)})
                    print(f"⚠️ Conflict: {fname} already exists.")
                    continue

                if dry_run:
                    print(f"Would move: {src_path}  →  {dest_path}")
                else:
                    shutil.move(str(src_path), str(dest_path))
                    print(f"Moved: {src_path}  →  {dest_path}")
                    moved_count += 1

            except Exception as e:
                errors.append({"file": str(src_path), "error": str(e)})

    # Write a move log for review (even in dry run mode)
    timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    log_dir = base_target / "_move_logs"
    log_dir.mkdir(parents=True, exist_ok=True)
    log_path = log_dir / f"move_log_{timestamp}.txt"

    with open(log_path, "w", encoding="utf-8") as f:
        f.write(f"Move operation timestamp: {timestamp}\n")
        f.write(f"Source: {source_dir}\n")
        f.write(f"Base target: {base_target}\n")
        f.write(f"Dry run: {dry_run}\n\n")
        f.write(f"Moved files: {moved_count}\n")
        f.write(f"Skipped .AAE files: {skipped_aae}\n")
        f.write(f"Skipped non-media files: {skipped_non_media}\n")
        f.write(f"Conflicts: {len(conflicts)}\n")
        f.write(f"Errors: {len(errors)}\n\n")

        if conflicts:
            f.write("Conflicts:\n")
            for c in conflicts:
                f.write(f"{c['source']}  ->  {c['destination']}\n")

        if errors:
            f.write("\nErrors:\n")
            for e in errors:
                f.write(f"{e['file']}: {e['error']}\n")

    print("\n✅ Summary:")
    print(f"- Moved files: {moved_count}")
    print(f"- Skipped .AAE files: {skipped_aae}")
    print(f"- Skipped non-media files: {skipped_non_media}")
    print(f"- Conflicts: {len(conflicts)}")
    print(f"- Errors: {len(errors)}")
    print(f"- Log saved to: {log_path}")
    print(f"{'No files were changed (dry run mode).' if dry_run else ''}")


def print_usage():
    print("Usage: python move_imported_files.py <source_dir> [--base <base_target>] [--dry-run]")
    print(r'Example: python move_imported_files.py "D:\Foto\_ImportIphone\PJ" --base "D:\Foto" --dry-run')


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print_usage()
        sys.exit(1)

    src = sys.argv[1]
    base = "D:/Foto"
    dry_run = "--dry-run" in sys.argv

    if "--base" in sys.argv:
        try:
            base = sys.argv[sys.argv.index("--base") + 1]
        except IndexError:
            print("Error: --base must be followed by a path.")
            sys.exit(1)

    move_files(src, base, dry_run=dry_run)

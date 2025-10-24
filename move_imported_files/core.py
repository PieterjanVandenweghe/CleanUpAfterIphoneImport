import os
import shutil
import datetime
from pathlib import Path

try:
    from PIL import Image, ExifTags
except Exception:
    raise RuntimeError("This package requires Pillow. Install with: pip install Pillow")

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


def move_files(source_dir: str, base_target: str = "D:/Foto", dry_run: bool = False, verbose: bool = False):
    source = Path(source_dir)
    if not source.exists() or not source.is_dir():
        raise FileNotFoundError(f"Source directory not found: {source_dir}")

    base_target = Path(base_target)
    conflicts, moved_count, skipped_aae, errors = [], 0, 0, []
    skipped_non_media = 0
    skipped_non_media_files = []
    scanned_files = 0

    for root, _, files in os.walk(source):
        for fname in files:
            scanned_files += 1
            ext = Path(fname).suffix.lower()
            src_path = Path(root) / fname

            if verbose:
                print(f"[scan] {src_path}  ext={ext}")

            if ext == ".aae":
                skipped_aae += 1
                if verbose:
                    print(f"[skip] .AAE file: {src_path}")
                continue

            if ext not in MEDIA_EXTENSIONS:
                skipped_non_media += 1
                skipped_non_media_files.append(str(src_path))
                if verbose:
                    print(f"[skip] non-media extension: {src_path}")
                continue

            try:
                dt = get_file_datetime(src_path)
                year = str(dt.year)
                month_folder = month_folder_name(dt)
                dest_dir = base_target / year / month_folder
                dest_dir.mkdir(parents=True, exist_ok=True)
                dest_path = dest_dir / fname

                if dest_path.exists():
                    conflicts.append({"source": str(src_path), "destination": str(dest_path)})
                    if verbose:
                        print(f"[conflict] destination exists: {dest_path}")
                    continue

                if dry_run:
                    if verbose:
                        print(f"[dry-run] would move: {src_path} -> {dest_path}")
                else:
                    shutil.move(str(src_path), str(dest_path))
                    if verbose:
                        print(f"[moved] {src_path} -> {dest_path}")
                    moved_count += 1

            except Exception as e:
                errors.append({"file": str(src_path), "error": str(e)})
                if verbose:
                    print(f"[error] {src_path}: {e}")

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

    return {
        "scanned": scanned_files,
        "moved": moved_count,
        "skipped_aae": skipped_aae,
        "skipped_non_media": skipped_non_media,
        "skipped_non_media_files": skipped_non_media_files,
        "conflicts": conflicts,
        "errors": errors,
        "log": str(log_path),
    }
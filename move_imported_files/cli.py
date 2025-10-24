import sys
import argparse
from .core import move_files

def main(argv=None):
    p = argparse.ArgumentParser(prog="move_imported_files")
    p.add_argument("source", help="Source directory to scan")
    p.add_argument("--base", default="D:/Foto", help="Base target directory")
    p.add_argument("--dry-run", action="store_true", help="Dry run (no files moved)")
    p.add_argument("--verbose", action="store_true", help="Show per-file decisions")
    args = p.parse_args(argv)

    try:
        result = move_files(args.source, args.base, dry_run=args.dry_run, verbose=args.verbose)
    except FileNotFoundError as e:
        print(f"ERROR: {e}")
        sys.exit(1)

    print("Summary:")
    print(f"- Scanned files: {result.get('scanned','?')}")
    print(f"- Moved files: {result['moved']}")
    print(f"- Skipped .AAE files: {result['skipped_aae']}")
    print(f"- Skipped non-media files: {result['skipped_non_media']}")
    if result.get("skipped_non_media_files"):
        print("  Skipped non-media (examples):")
        for s in result["skipped_non_media_files"][:20]:
            print(f"   - {s}")
    print(f"- Conflicts: {len(result['conflicts'])}")
    print(f"- Errors: {len(result['errors'])}")
    print(f"- Log saved to: {result['log']}")

if __name__ == "__main__":
    main()
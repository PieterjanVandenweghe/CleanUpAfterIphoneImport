import os
import sys

def delete_aae_files(root_dir):
    """
    Recursively deletes all .AAE files in the given directory and subdirectories.
    """
    deleted_files = 0

    for dirpath, _, filenames in os.walk(root_dir):
        for filename in filenames:
            if filename.lower().endswith('.aae'):
                file_path = os.path.join(dirpath, filename)
                try:
                    os.remove(file_path)
                    print(f"Deleted: {file_path}")
                    deleted_files += 1
                except Exception as e:
                    print(f"Failed to delete {file_path}: {e}")

    print(f"\nTotal .AAE files deleted: {deleted_files}")

if __name__ == "__main__":
    # Check if a directory argument was provided
    if len(sys.argv) != 2:
        print("Usage: python delete-aae.py <directory_path>")
        sys.exit(1)

    target_dir = sys.argv[1]

    if os.path.isdir(target_dir):
        delete_aae_files(target_dir)
    else:
        print("Invalid directory path.")

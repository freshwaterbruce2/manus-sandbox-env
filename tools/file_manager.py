"""file_manager.py — Reusable file management utilities for the Manus sandbox.

Provides high-level functions for file operations like searching,
calculating hashes, and managing temporary directories.
"""

import hashlib
import os
from pathlib import Path
from typing import List


def get_file_hash(filepath: str) -> str:
    """Calculate the SHA-256 hash of a file.

    Args:
        filepath: Path to the file.

    Returns:
        The hex digest of the SHA-256 hash.

    """
    sha256_hash = hashlib.sha256()
    with open(filepath, "rb") as f:
        # Read in chunks to handle large files
        for byte_block in iter(lambda: f.read(4096), b""):
            sha256_hash.update(byte_block)
    return sha256_hash.hexdigest()


def find_files_by_extension(directory: str, extension: str) -> List[str]:
    """Find all files with a specific extension in a directory.

    Args:
        directory: The root directory to search.
        extension: The file extension to look for (e.g., '.py').

    Returns:
        A list of absolute file paths.

    """
    path = Path(directory)
    return [str(f.absolute()) for f in path.glob(f"**/*{extension}")]


if __name__ == "__main__":
    # Demo usage
    print("=== File Manager Demo ===")
    current_dir = os.getcwd()
    py_files = find_files_by_extension(current_dir, ".py")
    print(f"Found {len(py_files)} Python files in {current_dir}.")
    if py_files:
        first_file = py_files[0]
        print(f"Hash of {Path(first_file).name}: {get_file_hash(first_file)}")

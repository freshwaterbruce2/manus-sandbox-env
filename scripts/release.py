"""release.py — Semantic Versioning and Git Tagging script.

This script manages the repository's versioning. It ensures that
releases are properly tagged in Git and follow SemVer (Major.Minor.Patch).
"""

import subprocess
import sys
from typing import List, Optional


def run_command(cmd: str) -> str:
    """Run a shell command and return the output."""
    try:
        result = subprocess.run(cmd, shell=True, capture_output=True, text=True, check=True)
        return result.stdout.strip()
    except subprocess.CalledProcessError as e:
        print(f"Error running command '{cmd}': {e.stderr}")
        sys.exit(1)


def get_latest_tag() -> Optional[str]:
    """Return the most recent Git tag, or None if no tags exist."""
    try:
        # Get tags sorted by version number
        tags = run_command("git tag -l --sort=-v:refname")
        if not tags:
            return None
        return tags.split("\n")[0]
    except Exception:
        return None


def increment_version(version: str, part: str) -> str:
    """Increment a semantic version string.

    Args:
        version: The current version string (e.g., '1.0.0').
        part: The part to increment ('major', 'minor', or 'patch').

    Returns:
        The incremented version string.

    """
    # Remove 'v' prefix if present
    clean_version = version[1:] if version.startswith("v") else version
    parts: List[int] = [int(p) for p in clean_version.split(".")]

    if part == "major":
        parts[0] += 1
        parts[1] = 0
        parts[2] = 0
    elif part == "minor":
        parts[1] += 1
        parts[2] = 0
    elif part == "patch":
        parts[2] += 1
    else:
        print(f"Invalid part to increment: {part}")
        sys.exit(1)

    return f"v{parts[0]}.{parts[1]}.{parts[2]}"


def main() -> None:
    """Run the release management process."""
    if len(sys.argv) < 2:
        print("Usage: python3 release.py [major|minor|patch|show]")
        sys.exit(1)

    action = sys.argv[1].lower()
    latest_tag = get_latest_tag()

    if action == "show":
        print(f"Latest release: {latest_tag if latest_tag else 'None'}")
        return

    if not latest_tag:
        print("No tags found. Initializing with v1.0.0.")
        new_version = "v1.0.0"
    else:
        new_version = increment_version(latest_tag, action)

    print(f"Current version: {latest_tag if latest_tag else 'N/A'}")
    print(f"New version    : {new_version}")

    # Confirm and tag
    confirm = input(f"Create tag {new_version}? (y/n): ").lower()
    if confirm == "y":
        run_command(f"git tag -a {new_version} -m 'Release {new_version}'")
        print(f"Tag {new_version} created locally.")
        print(f"To push, run: git push origin {new_version}")
    else:
        print("Release aborted.")


if __name__ == "__main__":
    main()

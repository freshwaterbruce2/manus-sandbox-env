#!/usr/bin/env python3
"""setup_hooks.py — Setup script for Manus sandbox repository hooks.

Installs the pre-commit hook into the .git/hooks directory.
"""

import os
import shutil
from pathlib import Path


def main() -> None:
    """Install the pre-commit hook into the .git/hooks directory."""
    # Ensure we are in the repository root
    repo_root = Path(__file__).parent.parent.absolute()
    os.chdir(repo_root)

    hooks_dir = repo_root / ".git" / "hooks"
    pre_commit_hook = hooks_dir / "pre-commit"
    source_script = repo_root / "scripts" / "pre_commit.py"

    if not hooks_dir.exists():
        print(f"Error: {hooks_dir} does not exist. Are you in a Git repository?")
        return

    print(f"Installing pre-commit hook to {pre_commit_hook}...")

    # Copy the script to the hooks directory
    shutil.copy(source_script, pre_commit_hook)

    # Make the hook executable
    pre_commit_hook.chmod(0o755)

    print("✅ Pre-commit hook installed successfully.")


if __name__ == "__main__":
    main()

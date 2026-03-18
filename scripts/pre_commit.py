#!/usr/bin/env python3
"""pre_commit.py — Git pre-commit hook for the Manus sandbox.

This script is called by Git before every commit. It runs the
Quality Gate to ensure that no non-compliant code is committed.
"""

import os
import subprocess
import sys
from pathlib import Path


def main() -> None:
    """Run the Quality Gate check as a pre-commit hook."""
    # This script is copied to .git/hooks/pre-commit
    # We need to find the repo root relative to this script's location
    # .git/hooks/pre-commit -> repo_root is two levels up
    # Wait, the script is COPIED, not symlinked.
    # We can use the GIT_DIR environment variable or find the .git directory.

    # Git sets the current working directory to the repo root during hooks
    repo_root = Path(os.getcwd()).absolute()
    os.chdir(repo_root)

    print(f"Running pre-commit Quality Gate check in {repo_root}...")

    # Path to the quality gate script
    quality_gate_script = repo_root / "scripts" / "quality_gate.py"

    if not quality_gate_script.exists():
        print(f"Error: Quality Gate script not found at {quality_gate_script}")
        sys.exit(1)

    # Run the quality gate
    result = subprocess.run([sys.executable, str(quality_gate_script)], check=False)

    if result.returncode != 0:
        print("\n🚨 PRE-COMMIT CHECK FAILED: Commit aborted.")
        print("Please fix the issues reported by the Quality Gate.")
        sys.exit(1)

    print("\n✅ PRE-COMMIT CHECK PASSED: Proceeding with commit.")
    sys.exit(0)


if __name__ == "__main__":
    main()

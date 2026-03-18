#!/usr/bin/env python3
"""quality_gate.py — The Manus Sandbox Quality Gate.

This script enforces strict code and documentation standards.
It runs:
1. Ruff (Python Formatting & Linting)
2. Mypy (Static Type Checking)
3. Markdownlint (Markdown Documentation Standards)

Any failure here prevents a commit or merge.
"""

import os
import subprocess
import sys
from pathlib import Path
from typing import Tuple


def run_command(cmd: str, description: str) -> Tuple[bool, str]:
    """Run a shell command and return (success, output).

    Args:
        cmd: The shell command to execute.
        description: A human-readable description of the command.

    Returns:
        A tuple of (success_boolean, combined_stdout_stderr).

    """
    print(f"--- Running {description} ---")
    try:
        # Use check=False to capture non-zero exit codes as failures
        result = subprocess.run(cmd, shell=True, capture_output=True, text=True, check=False)
        if result.returncode == 0:
            print(f"✅ {description} passed.")
            return True, result.stdout
        else:
            print(f"❌ {description} failed.")
            if result.stdout:
                print(f"STDOUT:\n{result.stdout}")
            if result.stderr:
                print(f"STDERR:\n{result.stderr}")
            return False, result.stdout + result.stderr
    except Exception as e:
        print(f"❌ Error running {description}: {e}")
        return False, str(e)


def main() -> None:
    """Execute the quality gate checks for the entire repository."""
    # Ensure we are in the repository root
    repo_root = Path(__file__).parent.parent.absolute()
    os.chdir(repo_root)

    print(f"Starting Quality Gate check in: {repo_root}\n")

    overall_success = True

    # 1. Python Formatting (Ruff)
    success, _ = run_command("ruff format --check .", "Python Formatting (Ruff)")
    if not success:
        overall_success = False

    # 2. Python Linting (Ruff)
    success, _ = run_command("ruff check .", "Python Linting (Ruff)")
    if not success:
        overall_success = False

    # 3. Static Type Checking (Mypy)
    success, _ = run_command("mypy .", "Static Type Checking (Mypy)")
    if not success:
        overall_success = False

    # 4. Automated Unit Testing (pytest)
    success, _ = run_command("PYTHONPATH=. pytest", "Automated Unit Testing (pytest)")
    if not success:
        overall_success = False

    # 5. Auto-Documentation Generation
    success, _ = run_command("python3 scripts/autodoc.py", "Auto-Documentation Generation")
    if not success:
        overall_success = False

    # 6. Markdown Linting (markdownlint)
    # We check all .md files excluding .git and node_modules
    success, _ = run_command(
        "markdownlint '**/*.md' --ignore 'node_modules'", "Markdown Linting (markdownlint)"
    )
    if not success:
        overall_success = False

    print("\n" + "=" * 40)
    if overall_success:
        print("🎉 QUALITY GATE PASSED: Repository is clean.")
        sys.exit(0)
    else:
        print("🚨 QUALITY GATE FAILED: Please fix the issues above.")
        sys.exit(1)


if __name__ == "__main__":
    main()

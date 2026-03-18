#!/usr/bin/env python3
"""manus_cli.py — Unified CLI wrapper for the Manus sandbox environment.

Provides a single entry point for all repository tasks:
- check: Run the Quality Gate.
- test: Run unit tests with pytest.
- doc: Generate LIBRARY.md with autodoc.
- release: Manage semantic versioning and tagging.
- info: Display sandbox environment information.
"""

import argparse
import os
import subprocess
import sys
from pathlib import Path


def run_command(cmd: str) -> None:
    """Run a shell command and exit with its return code."""
    try:
        # We use shell=True to allow for complex commands and aliases
        result = subprocess.run(cmd, shell=True, check=False)
        sys.exit(result.returncode)
    except Exception as e:
        print(f"Error executing command: {e}")
        sys.exit(1)


def main() -> None:
    """Run the Manus CLI entry point."""
    # Ensure we are in the repository root
    repo_root = Path(__file__).parent.parent.absolute()
    os.chdir(repo_root)

    parser = argparse.ArgumentParser(
        description="Manus Sandbox CLI — Unified Repository Management",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Commands:
  check      Run the full Quality Gate (formatting, linting, typing, testing, autodoc).
  test       Run unit tests with pytest and coverage reporting.
  doc        Regenerate the LIBRARY.md documentation.
  release    Manage semantic versioning (major|minor|patch|show).
  info       Display sandbox environment information.
        """,
    )
    parser.add_argument(
        "command",
        choices=["check", "test", "doc", "release", "info"],
        help="Command to run",
    )
    parser.add_argument(
        "args",
        nargs=argparse.REMAINDER,
        help="Additional arguments for the command",
    )

    if len(sys.argv) < 2:
        parser.print_help()
        sys.exit(1)

    args = parser.parse_args()

    if args.command == "check":
        run_command("python3 scripts/quality_gate.py")
    elif args.command == "test":
        run_command("PYTHONPATH=. pytest")
    elif args.command == "doc":
        run_command("python3 scripts/autodoc.py")
    elif args.command == "release":
        release_args = " ".join(args.args) if args.args else "show"
        run_command(f"python3 scripts/release.py {release_args}")
    elif args.command == "info":
        run_command("python3 scripts/sandbox_info.py")


if __name__ == "__main__":
    main()

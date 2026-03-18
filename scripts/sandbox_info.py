#!/usr/bin/env python3
"""
sandbox_info.py — Manus Sandbox Environment Inspector

Prints a summary of the current sandbox state: OS, Python version,
installed packages, disk usage, and GitHub auth status.
"""

import subprocess
import sys
import platform
import shutil
import os
from datetime import datetime


def run(cmd):
    """Run a shell command and return stdout."""
    try:
        result = subprocess.run(cmd, shell=True, capture_output=True, text=True, timeout=10)
        return result.stdout.strip()
    except Exception as e:
        return f"<error: {e}>"


def section(title):
    width = 50
    print(f"\n{'=' * width}")
    print(f"  {title}")
    print(f"{'=' * width}")


def main():
    print(f"\n{'#' * 50}")
    print(f"  Manus Sandbox Info — {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"{'#' * 50}")

    section("System")
    print(f"  OS       : {platform.system()} {platform.release()}")
    print(f"  Machine  : {platform.machine()}")
    print(f"  Hostname : {platform.node()}")
    print(f"  User     : {os.environ.get('USER', 'unknown')}")

    section("Python")
    print(f"  Version  : {sys.version.split()[0]}")
    print(f"  Exec     : {sys.executable}")

    section("Disk Usage")
    total, used, free = shutil.disk_usage("/")
    print(f"  Total    : {total // (1024**3)} GB")
    print(f"  Used     : {used // (1024**3)} GB")
    print(f"  Free     : {free // (1024**3)} GB")

    section("GitHub Auth")
    gh_status = run("gh auth status 2>&1 | head -3")
    for line in gh_status.splitlines():
        print(f"  {line.strip()}")

    section("Git Config")
    git_user = run("git config --global user.name")
    git_email = run("git config --global user.email")
    print(f"  Name     : {git_user}")
    print(f"  Email    : {git_email}")

    section("Recent Repos")
    repos = run("gh repo list --limit 5 --json name,isPrivate,updatedAt --jq '.[] | [.name, (if .isPrivate then \"private\" else \"public\" end), .updatedAt] | @tsv'")
    for line in repos.splitlines():
        parts = line.split("\t")
        if len(parts) >= 2:
            print(f"  [{parts[1]:7s}] {parts[0]}")

    print(f"\n{'#' * 50}\n")


if __name__ == "__main__":
    main()

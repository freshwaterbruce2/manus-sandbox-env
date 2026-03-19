#!/usr/bin/env python3
"""CLI test runner with rich output and category selection.

Usage:
    python run_tests.py --all
    python run_tests.py --agent --api
    python run_tests.py --sqlite --build
"""

from __future__ import annotations

import argparse
import subprocess
import sys
import time
from dataclasses import dataclass

try:
    from rich.console import Console
    from rich.table import Table
    from rich.panel import Panel
except ImportError:
    print("ERROR: 'rich' not installed. Run: pip install rich")
    sys.exit(1)

console = Console()


@dataclass
class TestCategory:
    """A test category with its pytest target and description."""

    name: str
    file: str
    description: str
    markers: str = ""


CATEGORIES: dict[str, TestCategory] = {
    "agent": TestCategory(
        name="Agent Validation",
        file="tests/test_agent_validation.py",
        description="Syntax checks, schema validation, complexity, placeholders",
    ),
    "api": TestCategory(
        name="API Smoke",
        file="tests/test_api_smoke.py",
        description="Health endpoints, response times, timeout handling",
        markers="requires_server",
    ),
    "sqlite": TestCategory(
        name="SQLite Integrity",
        file="tests/test_sqlite_integrity.py",
        description="PRAGMA checks, FK validation, schema drift, row counts",
        markers="requires_db",
    ),
    "build": TestCategory(
        name="Build Verification",
        file="tests/test_build_verification.py",
        description="pnpm build, tsc --noEmit, lockfile integrity",
        markers="requires_monorepo",
    ),
}


@dataclass
class CategoryResult:
    """Result of running a test category."""

    name: str
    passed: int
    failed: int
    skipped: int
    duration: float
    exit_code: int


def run_category(cat: TestCategory) -> CategoryResult:
    """Run a single test category and capture results."""
    console.print(f"\n[bold cyan]Running: {cat.name}[/bold cyan]")
    console.print(f"  [dim]{cat.description}[/dim]")

    start = time.monotonic()
    cmd = [sys.executable, "-m", "pytest", cat.file, "-v", "--tb=short", "-q"]

    try:
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=300)
    except subprocess.TimeoutExpired:
        elapsed = time.monotonic() - start
        console.print(f"  [red]TIMEOUT after {elapsed:.1f}s[/red]")
        return CategoryResult(cat.name, 0, 0, 0, elapsed, -1)

    elapsed = time.monotonic() - start
    stdout = result.stdout

    # Parse pytest summary line: "X passed, Y failed, Z skipped"
    passed = failed = skipped = 0
    for line in stdout.splitlines():
        if "passed" in line or "failed" in line or "skipped" in line:
            import re

            m_p = re.search(r"(\d+) passed", line)
            m_f = re.search(r"(\d+) failed", line)
            m_s = re.search(r"(\d+) skipped", line)
            if m_p:
                passed = int(m_p.group(1))
            if m_f:
                failed = int(m_f.group(1))
            if m_s:
                skipped = int(m_s.group(1))

    # Print failures inline
    if result.returncode != 0 and result.stdout:
        for line in result.stdout.splitlines():
            if "FAILED" in line or "ERROR" in line:
                console.print(f"  [red]{line.strip()}[/red]")

    status = "[green]PASS[/green]" if result.returncode == 0 else "[red]FAIL[/red]"
    console.print(f"  {status} ({passed}p/{failed}f/{skipped}s) in {elapsed:.1f}s")

    return CategoryResult(cat.name, passed, failed, skipped, elapsed, result.returncode)


def print_summary(results: list[CategoryResult]) -> None:
    """Print a summary table of all category results."""
    table = Table(title="Test Summary", show_header=True, header_style="bold magenta")
    table.add_column("Category", style="cyan", min_width=20)
    table.add_column("Passed", justify="right", style="green")
    table.add_column("Failed", justify="right", style="red")
    table.add_column("Skipped", justify="right", style="yellow")
    table.add_column("Time", justify="right")
    table.add_column("Status", justify="center")

    total_p = total_f = total_s = 0
    total_time = 0.0

    for r in results:
        status = "[green]PASS[/green]" if r.exit_code == 0 else "[red]FAIL[/red]"
        if r.exit_code == -1:
            status = "[yellow]TIMEOUT[/yellow]"
        table.add_row(
            r.name,
            str(r.passed),
            str(r.failed),
            str(r.skipped),
            f"{r.duration:.1f}s",
            status,
        )
        total_p += r.passed
        total_f += r.failed
        total_s += r.skipped
        total_time += r.duration

    table.add_section()
    overall = "[green]ALL PASS[/green]" if total_f == 0 else "[red]FAILURES[/red]"
    table.add_row(
        "[bold]Total[/bold]",
        f"[bold]{total_p}[/bold]",
        f"[bold]{total_f}[/bold]",
        f"[bold]{total_s}[/bold]",
        f"[bold]{total_time:.1f}s[/bold]",
        overall,
    )

    console.print()
    console.print(table)


def main() -> int:
    """Parse args and run selected test categories."""
    parser = argparse.ArgumentParser(description="VibeTech Test Runner")
    parser.add_argument("--agent", action="store_true", help="Agent validation tests")
    parser.add_argument("--api", action="store_true", help="API smoke tests")
    parser.add_argument("--sqlite", action="store_true", help="SQLite integrity tests")
    parser.add_argument("--build", action="store_true", help="Build verification tests")
    parser.add_argument("--all", action="store_true", help="Run all categories")
    args = parser.parse_args()

    selected = []
    if args.all:
        selected = list(CATEGORIES.keys())
    else:
        for key in CATEGORIES:
            if getattr(args, key, False):
                selected.append(key)

    if not selected:
        console.print(Panel(
            "[yellow]No categories selected.[/yellow]\n"
            "Use --agent, --api, --sqlite, --build, or --all",
            title="VibeTech Test Runner",
        ))
        return 1

    console.print(Panel(
        f"Running {len(selected)} test categories: {', '.join(selected)}",
        title="VibeTech Test Runner",
        style="bold blue",
    ))

    results = [run_category(CATEGORIES[key]) for key in selected]
    print_summary(results)

    return 1 if any(r.exit_code != 0 and r.exit_code != -1 for r in results) else 0


if __name__ == "__main__":
    sys.exit(main())

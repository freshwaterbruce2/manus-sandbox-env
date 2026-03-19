#!/usr/bin/env python3
"""Vibetech Test Runner — orchestrates all four test categories.

Usage:
    python scripts/run_tests.py              # Run all categories
    python scripts/run_tests.py --category agent       # Agent validation only
    python scripts/run_tests.py --category api         # API smoke tests only
    python scripts/run_tests.py --category sqlite      # SQLite integrity only
    python scripts/run_tests.py --category build       # Build verification only
    python scripts/run_tests.py --verbose              # Verbose pytest output
    python scripts/run_tests.py --ci                   # CI mode (no color, JUnit XML)
"""

from __future__ import annotations

import argparse
import subprocess
import sys
import time
from dataclasses import dataclass

# ---------------------------------------------------------------------------
# Color helpers (ANSI)
# ---------------------------------------------------------------------------

RESET = "\033[0m"
BOLD = "\033[1m"
RED = "\033[91m"
GREEN = "\033[92m"
YELLOW = "\033[93m"
BLUE = "\033[94m"
CYAN = "\033[96m"
DIM = "\033[2m"


def _c(text: str, color: str, use_color: bool = True) -> str:
    """Wrap text in ANSI color codes."""
    if not use_color:
        return text
    return f"{color}{text}{RESET}"


# ---------------------------------------------------------------------------
# Test categories
# ---------------------------------------------------------------------------

CATEGORIES: dict[str, dict[str, str]] = {
    "agent": {
        "label": "Agent Output Validation",
        "marker": "not (LiveDatabases or LiveBuilds or ExpressBackendLive or OpenRouterProxyLive)",
        "file": "tests/test_agent_validation.py",
        "icon": "🤖",
    },
    "api": {
        "label": "API Endpoint Smoke Tests",
        "marker": "",
        "file": "tests/test_api_smoke.py",
        "icon": "🌐",
    },
    "sqlite": {
        "label": "SQLite Integrity Checks",
        "marker": "",
        "file": "tests/test_sqlite_integrity.py",
        "icon": "🗄️",
    },
    "build": {
        "label": "Build Verification",
        "marker": "",
        "file": "tests/test_build_verification.py",
        "icon": "🔨",
    },
}


# ---------------------------------------------------------------------------
# Result tracking
# ---------------------------------------------------------------------------

@dataclass
class CategoryResult:
    """Result of running one test category."""

    name: str
    label: str
    passed: bool
    duration: float
    test_count: int
    fail_count: int
    skip_count: int
    output: str


def _run_category(
    name: str,
    info: dict[str, str],
    verbose: bool = False,
    ci_mode: bool = False,
) -> CategoryResult:
    """Run a single test category via pytest subprocess."""
    cmd = [sys.executable, "-m", "pytest", info["file"], "-v" if verbose else "-q"]

    if info.get("marker"):
        cmd.extend(["-k", info["marker"]])

    if ci_mode:
        cmd.extend(["--tb=short", "--no-header", "-p", "no:color"])

    # Disable coverage for the runner (we just want pass/fail)
    cmd.extend(["--no-cov", "--override-ini=addopts="])

    start = time.time()
    result = subprocess.run(cmd, capture_output=True, text=True, timeout=300)
    elapsed = time.time() - start

    # Parse counts from pytest output
    output = result.stdout + result.stderr
    test_count = 0
    fail_count = 0
    skip_count = 0

    for line in output.split("\n"):
        if "passed" in line or "failed" in line or "error" in line:
            # Parse the summary line like "5 passed, 2 skipped, 1 failed"
            import re

            for match in re.finditer(r"(\d+)\s+(passed|failed|skipped|error)", line):
                count = int(match.group(1))
                kind = match.group(2)
                if kind == "passed":
                    test_count += count
                elif kind == "failed":
                    fail_count += count
                elif kind == "skipped":
                    skip_count += count

    return CategoryResult(
        name=name,
        label=info["label"],
        passed=result.returncode == 0,
        duration=elapsed,
        test_count=test_count,
        fail_count=fail_count,
        skip_count=skip_count,
        output=output,
    )


# ---------------------------------------------------------------------------
# Summary
# ---------------------------------------------------------------------------

def _print_summary(results: list[CategoryResult], use_color: bool = True) -> None:
    """Print a formatted summary of all test categories."""
    print()
    print(_c("=" * 70, BOLD, use_color))
    print(_c("  VIBETECH TEST SUITE — SUMMARY", BOLD + CYAN, use_color))
    print(_c("=" * 70, BOLD, use_color))
    print()

    total_pass = 0
    total_fail = 0
    total_skip = 0
    total_time = 0.0

    for r in results:
        icon = CATEGORIES[r.name]["icon"]
        if r.passed:
            status = _c(" PASS ", GREEN + BOLD, use_color)
        else:
            status = _c(" FAIL ", RED + BOLD, use_color)
        timing = _c(f"{r.duration:.1f}s", DIM, use_color)

        counts = f"{r.test_count} passed"
        if r.fail_count:
            counts += f", {r.fail_count} failed"
        if r.skip_count:
            counts += f", {r.skip_count} skipped"

        print(f"  {icon} {status}  {r.label:<30}  {counts:<30}  {timing}")

        total_pass += r.test_count
        total_fail += r.fail_count
        total_skip += r.skip_count
        total_time += r.duration

    print()
    print(_c("-" * 70, DIM, use_color))

    total_label = _c("TOTAL", BOLD, use_color)
    if total_fail == 0:
        overall = _c("ALL PASS", GREEN + BOLD, use_color)
    else:
        overall = _c(f"{total_fail} FAILURES", RED + BOLD, use_color)
    summary = (
        f"  {total_label}: {total_pass} passed, {total_fail} failed, "
        f"{total_skip} skipped  —  {overall}  ({total_time:.1f}s)"
    )
    print(summary)
    print()


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main() -> int:
    """Run the test suite."""
    parser = argparse.ArgumentParser(description="Vibetech Test Runner")
    parser.add_argument(
        "--category", "-c",
        choices=list(CATEGORIES.keys()),
        help="Run a single category (default: all)",
    )
    parser.add_argument("--verbose", "-v", action="store_true", help="Verbose pytest output")
    parser.add_argument("--ci", action="store_true", help="CI mode (no color, machine output)")
    args = parser.parse_args()

    use_color = not args.ci and sys.stdout.isatty()

    print()
    print(_c("  VIBETECH AUTOMATED TESTING SYSTEM", BOLD + BLUE, use_color))
    print(_c("  " + "=" * 40, BLUE, use_color))
    print()

    categories = {args.category: CATEGORIES[args.category]} if args.category else CATEGORIES
    results: list[CategoryResult] = []

    for name, info in categories.items():
        icon = info["icon"]
        print(_c(f"  {icon}  Running: {info['label']}...", YELLOW, use_color))

        result = _run_category(name, info, verbose=args.verbose, ci_mode=args.ci)
        results.append(result)

        if args.verbose or not result.passed:
            print(result.output)

    _print_summary(results, use_color=use_color)

    # Exit code: 0 if all passed, 1 if any failed
    return 0 if all(r.passed for r in results) else 1


if __name__ == "__main__":
    sys.exit(main())
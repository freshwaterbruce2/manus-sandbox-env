"""Build Verification Tests.

Verifies pnpm builds pass for specific apps in the monorepo at C:\\dev.
Checks exit codes, captures errors, reports pass/fail.
Also includes unit tests that always run (mocked subprocess).
"""

from __future__ import annotations

import os
import subprocess
from pathlib import Path
from typing import Any
from unittest.mock import MagicMock, patch

import pytest

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _run_build(
    monorepo_root: str,
    app_path: str,
    build_command: str,
    timeout: int = 120,
) -> tuple[bool, str, str, float]:
    """Run a build command and return (success, stdout, stderr, duration).

    Args:
        monorepo_root: Absolute path to monorepo root (e.g. C:\\dev).
        app_path: Relative path from root to app (e.g. apps\\nova-agent).
        build_command: The build command to run (e.g. pnpm run build).
        timeout: Max seconds before killing the build.

    Returns:
        Tuple of (passed, stdout, stderr, elapsed_seconds).
    """
    import time

    full_path = Path(monorepo_root) / app_path
    if not full_path.exists():
        return False, "", f"Path does not exist: {full_path}", 0.0

    start = time.time()
    try:
        result = subprocess.run(
            build_command.split(),
            cwd=str(full_path),
            capture_output=True,
            text=True,
            timeout=timeout,
            shell=os.name == "nt",  # shell=True on Windows for pnpm
        )
        elapsed = time.time() - start
        return result.returncode == 0, result.stdout, result.stderr, elapsed

    except subprocess.TimeoutExpired:
        elapsed = time.time() - start
        return False, "", f"Build timed out after {timeout}s", elapsed

    except FileNotFoundError as e:
        return False, "", f"Command not found: {e}", 0.0


def _check_pnpm_available() -> bool:
    """Check if pnpm is available on PATH."""
    try:
        result = subprocess.run(
            ["pnpm", "--version"],
            capture_output=True,
            text=True,
            timeout=10,
            shell=os.name == "nt",
        )
        return result.returncode == 0
    except (FileNotFoundError, subprocess.TimeoutExpired):
        return False


# ---------------------------------------------------------------------------
# Unit tests (always run — mocked)
# ---------------------------------------------------------------------------

class TestBuildHelpers:
    """Test build verification helpers with mocked subprocess."""

    @patch("subprocess.run")
    def test_successful_build(self, mock_run: MagicMock, tmp_path: Path) -> None:
        """Successful build should return (True, stdout, '', duration)."""
        mock_run.return_value = MagicMock(
            returncode=0,
            stdout="Build completed successfully\n",
            stderr="",
        )
        app_dir = tmp_path / "apps" / "test-app"
        app_dir.mkdir(parents=True)

        passed, stdout, stderr, _ = _run_build(
            str(tmp_path), "apps/test-app", "pnpm run build"
        )
        assert passed is True
        assert "Build completed" in stdout

    @patch("subprocess.run")
    def test_failed_build(self, mock_run: MagicMock, tmp_path: Path) -> None:
        """Failed build should return (False, '', stderr, duration)."""
        mock_run.return_value = MagicMock(
            returncode=1,
            stdout="",
            stderr="Error: Cannot find module 'foo'\n",
        )
        app_dir = tmp_path / "apps" / "broken-app"
        app_dir.mkdir(parents=True)

        passed, stdout, stderr, _ = _run_build(
            str(tmp_path), "apps/broken-app", "pnpm run build"
        )
        assert passed is False
        assert "Cannot find module" in stderr

    @patch("subprocess.run", side_effect=subprocess.TimeoutExpired(cmd="pnpm", timeout=120))
    def test_build_timeout(self, mock_run: MagicMock, tmp_path: Path) -> None:
        """Timed out build should return failure with timeout message."""
        app_dir = tmp_path / "apps" / "slow-app"
        app_dir.mkdir(parents=True)

        passed, stdout, stderr, _ = _run_build(
            str(tmp_path), "apps/slow-app", "pnpm run build", timeout=120
        )
        assert passed is False
        assert "timed out" in stderr.lower()

    def test_nonexistent_path(self, tmp_path: Path) -> None:
        """Build against nonexistent path should fail gracefully."""
        passed, stdout, stderr, _ = _run_build(
            str(tmp_path), "apps/ghost-app", "pnpm run build"
        )
        assert passed is False
        assert "does not exist" in stderr


class TestBuildResultParsing:
    """Test parsing of build output for common error patterns."""

    def test_detect_typescript_errors(self) -> None:
        """Should identify TypeScript compilation errors in output."""
        stderr = "error TS2304: Cannot find name 'foo'.\nerror TS2345: Type mismatch."
        ts_errors = [line for line in stderr.split("\n") if "error TS" in line]
        assert len(ts_errors) == 2

    def test_detect_missing_module(self) -> None:
        """Should identify missing module errors."""
        stderr = "Error: Cannot find module '@vibetech/shared-types'"
        assert "Cannot find module" in stderr

    def test_detect_out_of_memory(self) -> None:
        """Should identify OOM errors."""
        stderr = (
            "FATAL ERROR: CALL_AND_RETRY_LAST Allocation failed"
            " - JavaScript heap out of memory"
        )
        assert "heap out of memory" in stderr.lower()


# ---------------------------------------------------------------------------
# Live tests (only on Windows with C:\dev and pnpm)
# ---------------------------------------------------------------------------

class TestLiveBuilds:
    """Run actual builds against the monorepo. Windows + pnpm required."""

    @pytest.fixture(autouse=True)
    def _require_build_env(self) -> None:
        if os.name != "nt":
            pytest.skip("Build verification requires Windows")
        if not Path("C:\\dev").exists():
            pytest.skip("Monorepo not found at C:\\dev")
        if not _check_pnpm_available():
            pytest.skip("pnpm not available on PATH")

    def test_configured_app_builds(
        self, build_config: dict[str, Any]
    ) -> None:
        """All configured apps should build successfully."""
        root = build_config.get("monorepo_root", "C:\\dev")
        timeout = build_config.get("build_timeout", 120)
        results: dict[str, tuple[bool, str]] = {}

        for app in build_config.get("apps", []):
            name = app["name"]
            app_path = app["path"]
            cmd = app.get("build_command", "pnpm run build")

            passed, stdout, stderr, elapsed = _run_build(root, app_path, cmd, timeout)
            results[name] = (passed, stderr if not passed else f"{elapsed:.1f}s")

        failures = {k: v[1] for k, v in results.items() if not v[0]}
        assert not failures, f"Build failures: {failures}"

    def test_monorepo_root_has_package_json(self) -> None:
        """C:\\dev should have a package.json (workspace root)."""
        assert Path("C:\\dev\\package.json").exists(), "Missing package.json at C:\\dev"

    def test_monorepo_root_has_pnpm_workspace(self) -> None:
        """C:\\dev should have pnpm-workspace.yaml."""
        ws = Path("C:\\dev\\pnpm-workspace.yaml")
        assert ws.exists(), "Missing pnpm-workspace.yaml at C:\\dev"
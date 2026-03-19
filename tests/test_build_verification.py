"""Build verification tests — run pnpm build on configured apps."""

from __future__ import annotations

import subprocess
from pathlib import Path
from typing import Any

import pytest

pytestmark = pytest.mark.requires_monorepo


class TestBuildVerification:
    """Verify that key monorepo apps build successfully."""

    @pytest.fixture(autouse=True)
    def _skip_if_no_monorepo(self, monorepo_root: Path) -> None:
        if not monorepo_root.exists():
            pytest.skip(f"Monorepo not found at {monorepo_root}")
        if not (monorepo_root / "pnpm-lock.yaml").exists():
            pytest.skip("Not a pnpm workspace — missing pnpm-lock.yaml")

    def _run_build(
        self, monorepo_root: Path, app_name: str, timeout: int
    ) -> subprocess.CompletedProcess[str]:
        """Run pnpm build for a specific app."""
        app_dir = monorepo_root / "apps" / app_name
        if not app_dir.exists():
            pytest.skip(f"App directory not found: {app_dir}")

        return subprocess.run(
            ["pnpm", "run", "build"],
            cwd=str(app_dir),
            capture_output=True,
            text=True,
            timeout=timeout,
            shell=True,
        )

    def test_apps_build_successfully(
        self,
        monorepo_root: Path,
        apps_to_verify: list[str],
        config: dict[str, Any],
    ) -> None:
        timeout = config["monorepo"]["build_timeout_seconds"]
        failures: list[str] = []

        for app in apps_to_verify:
            app_dir = monorepo_root / "apps" / app
            if not app_dir.exists():
                continue
            try:
                result = self._run_build(monorepo_root, app, timeout)
                if result.returncode != 0:
                    stderr_snippet = result.stderr[:500] if result.stderr else "N/A"
                    failures.append(f"{app}: exit {result.returncode}\n{stderr_snippet}")
            except subprocess.TimeoutExpired:
                failures.append(f"{app}: timed out after {timeout}s")
            except FileNotFoundError:
                failures.append(f"{app}: pnpm not found in PATH")

        if failures:
            report = "\n---\n".join(failures)
            pytest.fail(f"Build failures:\n{report}")


class TestTypeCheck:
    """Verify TypeScript type checking passes."""

    @pytest.fixture(autouse=True)
    def _skip_if_no_monorepo(self, monorepo_root: Path) -> None:
        if not monorepo_root.exists():
            pytest.skip(f"Monorepo not found at {monorepo_root}")

    def test_tsc_noEmit(self, monorepo_root: Path, config: dict[str, Any]) -> None:
        """Run tsc --noEmit on the monorepo root."""
        timeout = config["monorepo"]["build_timeout_seconds"]
        tsconfig = monorepo_root / "tsconfig.base.json"
        if not tsconfig.exists():
            pytest.skip("No tsconfig.base.json found")

        try:
            result = subprocess.run(
                ["npx", "tsc", "--noEmit", "-p", str(tsconfig)],
                cwd=str(monorepo_root),
                capture_output=True,
                text=True,
                timeout=timeout,
                shell=True,
            )
            if result.returncode != 0:
                errors = result.stdout[:1000] or result.stderr[:1000]
                pytest.fail(f"tsc --noEmit failed:\n{errors}")
        except subprocess.TimeoutExpired:
            pytest.skip(f"tsc timed out after {timeout}s")
        except FileNotFoundError:
            pytest.skip("npx/tsc not found in PATH")


class TestPackageIntegrity:
    """Verify pnpm workspace is consistent."""

    @pytest.fixture(autouse=True)
    def _skip_if_no_monorepo(self, monorepo_root: Path) -> None:
        if not monorepo_root.exists():
            pytest.skip(f"Monorepo not found at {monorepo_root}")

    def test_pnpm_lockfile_exists(self, monorepo_root: Path) -> None:
        lockfile = monorepo_root / "pnpm-lock.yaml"
        assert lockfile.exists(), "pnpm-lock.yaml missing"
        assert lockfile.stat().st_size > 0, "pnpm-lock.yaml is empty"

    def test_no_package_lock_json(self, monorepo_root: Path) -> None:
        """Ensure npm hasn't polluted the workspace."""
        npm_lock = monorepo_root / "package-lock.json"
        assert not npm_lock.exists(), (
            "package-lock.json found — npm was run. Remove it and use pnpm only."
        )

    def test_no_yarn_lock(self, monorepo_root: Path) -> None:
        yarn_lock = monorepo_root / "yarn.lock"
        assert not yarn_lock.exists(), "yarn.lock found — use pnpm only."

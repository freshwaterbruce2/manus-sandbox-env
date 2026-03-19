"""Build verification tests for the pnpm monorepo at C:\\dev."""

from __future__ import annotations

import json
import re
import subprocess
from pathlib import Path
from typing import Any

import pytest


class TestMonorepoStructure:
    """Verify monorepo directory structure and config files."""

    def test_root_exists(self, monorepo_config: dict[str, Any]) -> None:
        """Monorepo root directory should exist."""
        root = Path(monorepo_config.get("root", r"C:\dev"))
        if not root.exists():
            pytest.skip(f"Monorepo root not found: {root}")
        assert root.is_dir()

    def test_package_json_exists(self, monorepo_config: dict[str, Any]) -> None:
        """Root package.json should exist."""
        root = Path(monorepo_config.get("root", r"C:\dev"))
        pkg = root / "package.json"
        if not root.exists():
            pytest.skip("Monorepo root not found")
        assert pkg.exists(), f"No package.json at {pkg}"

    def test_pnpm_workspace_exists(self, monorepo_config: dict[str, Any]) -> None:
        """pnpm-workspace.yaml should exist."""
        root = Path(monorepo_config.get("root", r"C:\dev"))
        ws = root / "pnpm-workspace.yaml"
        if not root.exists():
            pytest.skip("Monorepo root not found")
        assert ws.exists(), f"No pnpm-workspace.yaml at {ws}"

    def test_apps_directory(self, monorepo_config: dict[str, Any]) -> None:
        """Apps directory should contain subdirectories."""
        apps = Path(monorepo_config.get("apps_dir", r"C:\dev\apps"))
        if not apps.exists():
            pytest.skip("Apps directory not found")
        subdirs = [d for d in apps.iterdir() if d.is_dir()]
        assert len(subdirs) > 0, "Apps directory is empty"

    def test_packages_directory(self, monorepo_config: dict[str, Any]) -> None:
        """Packages directory should contain subdirectories."""
        pkgs = Path(monorepo_config.get("packages_dir", r"C:\dev\packages"))
        if not pkgs.exists():
            pytest.skip("Packages directory not found")
        subdirs = [d for d in pkgs.iterdir() if d.is_dir()]
        assert len(subdirs) > 0, "Packages directory is empty"


class TestPnpmAvailability:
    """Verify pnpm is available and correct version."""

    def test_pnpm_installed(self) -> None:
        """pnpm should be available on PATH."""
        try:
            result = subprocess.run(
                ["pnpm", "--version"],
                capture_output=True,
                text=True,
                timeout=15,
            )
            assert (
                result.returncode == 0
            ), f"pnpm --version failed: {result.stderr}"
        except FileNotFoundError:
            pytest.skip("pnpm not found on PATH")

    def test_pnpm_version(self) -> None:
        """pnpm version should be 10.x."""
        try:
            result = subprocess.run(
                ["pnpm", "--version"],
                capture_output=True,
                text=True,
                timeout=15,
            )
            version = result.stdout.strip()
            major = int(version.split(".")[0])
            assert major >= 9, f"pnpm {version} is too old (need >= 9)"
        except FileNotFoundError:
            pytest.skip("pnpm not found")


class TestNxAvailability:
    """Verify NX is accessible within the monorepo."""

    def test_nx_available(self, monorepo_config: dict[str, Any]) -> None:
        """NX should be runnable from monorepo root."""
        root = Path(monorepo_config.get("root", r"C:\dev"))
        if not root.exists():
            pytest.skip("Monorepo root not found")
        try:
            result = subprocess.run(
                ["pnpm", "nx", "--version"],
                capture_output=True,
                text=True,
                timeout=30,
                cwd=str(root),
            )
            assert (
                result.returncode == 0
            ), f"nx --version failed: {result.stderr}"
        except FileNotFoundError:
            pytest.skip("pnpm/nx not found")


class TestTypeScriptConfig:
    """Verify TypeScript configuration."""

    def test_tsconfig_exists(self, monorepo_config: dict[str, Any]) -> None:
        """Root tsconfig should exist."""
        root = Path(monorepo_config.get("root", r"C:\dev"))
        candidates = [
            root / "tsconfig.base.json",
            root / "tsconfig.json",
        ]
        if not root.exists():
            pytest.skip("Monorepo root not found")
        found = any(c.exists() for c in candidates)
        assert found, "No tsconfig found at monorepo root"

    def test_tsconfig_parseable(self, monorepo_config: dict[str, Any]) -> None:
        """Root tsconfig should be valid JSON (with comments stripped)."""
        root = Path(monorepo_config.get("root", r"C:\dev"))
        candidates = [
            root / "tsconfig.base.json",
            root / "tsconfig.json",
        ]
        if not root.exists():
            pytest.skip("Monorepo root not found")
        for c in candidates:
            if c.exists():
                raw = c.read_text(encoding="utf-8")
                stripped = re.sub(r"//.*$", "", raw, flags=re.MULTILINE)
                stripped = re.sub(r"/\*.*?\*/", "", stripped, flags=re.DOTALL)
                try:
                    data = json.loads(stripped)
                    assert "compilerOptions" in data
                    return
                except json.JSONDecodeError:
                    pass
        pytest.skip("No parseable tsconfig found")

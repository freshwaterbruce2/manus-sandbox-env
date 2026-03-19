"""Agent Output Validation Tests.

Validates AI agent outputs (DeepSeek, Kimi) dropped into experiments/.
Checks: syntax validity, JSON schema, forbidden patterns, file size limits.
"""

from __future__ import annotations

import ast
import json
import re
from pathlib import Path
from typing import Any

import pytest


class TestAgentOutputSyntax:
    """Validate that agent-generated code files have valid syntax."""

    def test_python_files_parse(
        self, sample_experiment_dir: Path, agent_config: dict[str, Any]
    ) -> None:
        """All .py files in experiments should parse without SyntaxError."""
        py_files = list(sample_experiment_dir.glob("*.py"))
        assert py_files, "No Python files found in experiment directory"

        parse_results: dict[str, bool] = {}
        for f in py_files:
            source = f.read_text(encoding="utf-8")
            try:
                ast.parse(source, filename=str(f))
                parse_results[f.name] = True
            except SyntaxError:
                parse_results[f.name] = False

        # Report all results — don't fail on first
        failures = [name for name, ok in parse_results.items() if not ok]
        # We expect broken_agent_output.py to fail — that's the fixture
        # Real runs against experiments/ should have zero failures
        assert "broken_agent_output.py" in failures, (
            "Expected broken_agent_output.py to have syntax errors"
        )

    def test_valid_python_files_contain_expected_patterns(
        self, sample_experiment_dir: Path, agent_config: dict[str, Any]
    ) -> None:
        """Valid Python files should contain at least one expected pattern."""
        patterns = agent_config.get("expected_python_patterns", ["def ", "class ", "import "])
        py_files = list(sample_experiment_dir.glob("*.py"))

        for f in py_files:
            source = f.read_text(encoding="utf-8")
            # Skip files with syntax errors
            try:
                ast.parse(source)
            except SyntaxError:
                continue

            has_pattern = any(p in source for p in patterns)
            assert has_pattern, (
                f"{f.name} contains no expected patterns: {patterns}"
            )

    def test_json_files_are_valid(self, sample_experiment_dir: Path) -> None:
        """All .json files should be valid JSON."""
        json_files = list(sample_experiment_dir.glob("*.json"))
        if not json_files:
            pytest.skip("No JSON files to validate")

        for f in json_files:
            content = f.read_text(encoding="utf-8")
            try:
                parsed = json.loads(content)
                assert isinstance(parsed, (dict, list)), (
                    f"{f.name}: JSON root must be object or array, got {type(parsed).__name__}"
                )
            except json.JSONDecodeError as e:
                pytest.fail(f"{f.name}: Invalid JSON — {e}")


class TestAgentOutputSecurity:
    """Check agent outputs for leaked secrets and forbidden patterns."""

    def test_no_forbidden_patterns(
        self, sample_experiment_dir: Path, agent_config: dict[str, Any]
    ) -> None:
        """Agent output files must not contain secrets or API keys."""
        forbidden = agent_config.get(
            "forbidden_patterns", ["API_KEY=", "SECRET=", "sk-"]
        )
        all_files = [
            f
            for f in sample_experiment_dir.iterdir()
            if f.is_file() and f.suffix in (".py", ".ts", ".tsx", ".js", ".json")
        ]

        violations: list[str] = []
        for f in all_files:
            content = f.read_text(encoding="utf-8")
            for pattern in forbidden:
                if pattern in content:
                    violations.append(f"{f.name} contains '{pattern}'")

        # leaky_output.py is expected to trigger
        assert any("leaky_output.py" in v for v in violations), (
            "Expected leaky_output.py to contain forbidden patterns"
        )

    def test_file_sizes_within_limit(
        self, sample_experiment_dir: Path, agent_config: dict[str, Any]
    ) -> None:
        """Agent output files should not exceed configured size limit."""
        max_size = agent_config.get("max_file_size", 1048576)  # 1MB default
        all_files = [f for f in sample_experiment_dir.iterdir() if f.is_file()]

        oversized = []
        for f in all_files:
            size = f.stat().st_size
            if size > max_size:
                oversized.append(f"{f.name}: {size} bytes (max: {max_size})")

        assert not oversized, f"Oversized files: {oversized}"


class TestAgentOutputStructure:
    """Validate structural properties of agent outputs."""

    def test_no_empty_files(self, sample_experiment_dir: Path) -> None:
        """Agent should not produce empty output files."""
        code_exts = {".py", ".ts", ".tsx", ".js", ".jsx", ".json"}
        empty_files = [
            f.name
            for f in sample_experiment_dir.iterdir()
            if f.is_file() and f.suffix in code_exts and f.stat().st_size == 0
        ]
        assert not empty_files, f"Empty agent output files: {empty_files}"

    def test_no_placeholder_tokens(self, sample_experiment_dir: Path) -> None:
        """Agent outputs should not contain common placeholder tokens."""
        placeholders = [
            r"\[your[\s-]?value[\s-]?here\]",
            r"\[TODO\]",
            r"\[PLACEHOLDER\]",
            r"<your[\s_-]?api[\s_-]?key>",
            r"INSERT_.*_HERE",
        ]
        code_exts = {".py", ".ts", ".tsx", ".js", ".jsx"}
        found: list[str] = []

        for f in sample_experiment_dir.iterdir():
            if f.is_file() and f.suffix in code_exts:
                content = f.read_text(encoding="utf-8")
                for pat in placeholders:
                    if re.search(pat, content, re.IGNORECASE):
                        found.append(f"{f.name} matches placeholder: {pat}")

        assert not found, f"Placeholder tokens found: {found}"


class TestExperimentsDirectory:
    """Tests that run against the actual experiments/ directory in the repo."""

    def test_experiments_dir_exists(self, experiments_dir: Path) -> None:
        """The experiments/ directory must exist."""
        assert experiments_dir.exists(), f"Missing: {experiments_dir}"
        assert experiments_dir.is_dir(), f"Not a directory: {experiments_dir}"

    def test_experiments_has_readme(self, experiments_dir: Path) -> None:
        """experiments/ should have a README for context."""
        readme = experiments_dir / "README.md"
        assert readme.exists(), "experiments/README.md missing"
# Manus Sandbox Environment

AI agent sandbox for GitHub automation experiments. This repo is a testbed for building, validating, and iterating on Python-based GitHub automation tools — from CLI wrappers and quality gates to feature flags and file utilities. Includes a comprehensive automated testing system.

## What's Here

```
manus-sandbox-env/
├── tools/             # Reusable Python modules (GitHub API, feature flags, file ops)
├── scripts/           # Automation runners (quality gate, release, pre-commit hooks)
├── experiments/       # Throwaway test scripts and AI agent experiments
├── tests/             # pytest suite — agent validation, API smoke, SQLite, build checks
├── config/            # Test configuration (endpoints, DB paths, schemas)
├── docs/              # Reports — testing results, compatibility, quality gate logs
├── .github/workflows/ # CI pipeline (lint, type-check, test, coverage)
├── pyproject.toml     # Ruff, mypy, pytest config + test dependencies
├── run_tests.py       # Test orchestrator with colored output and category selection
└── setup.sh           # One-shot environment bootstrap
```

## Quick Start

```bash
git clone https://github.com/freshwaterbruce2/manus-sandbox-env.git
cd manus-sandbox-env
pip install ruff mypy pytest pytest-cov requests pyyaml rich jsonschema
python scripts/quality_gate.py
```

## Automated Testing System

Four test categories covering the full stack:

**Agent Validation** (`tests/test_agent_validation.py`) — Validates AI agent outputs: JSON schema validation, Python/TypeScript syntax checking, code output parsing, response format verification.

**API Smoke Tests** (`tests/test_api_smoke.py`) — Express API (localhost:5177) and OpenRouter proxy (localhost:3001) health checks, response shape validation, latency assertions.

**SQLite Integrity** (`tests/test_sqlite_integrity.py`) — PRAGMA integrity_check on all databases in D:\databases\ and D:\learning-system\, schema validation, row count monitoring.

**Build Verification** (`tests/test_build_verification.py`) — pnpm monorepo structure at C:\dev: package.json, pnpm-workspace.yaml, tsconfig, pnpm/NX availability and version checks.

### Running Tests

```bash
python run_tests.py                    # All categories
python run_tests.py -c agent api       # Specific categories
python run_tests.py --list             # List categories
python run_tests.py --verbose          # Full pytest output
pytest tests/ -v --tb=short            # Direct pytest
```

### Configuration

Edit `config/test_config.yaml` to match your environment — API endpoints, database paths, monorepo location, and validation thresholds.

## Tools

| Module | Purpose |
|---|---|
| `tools/github_helper.py` | GitHub CLI wrapper — repos, issues, PRs, releases, branch ops |
| `tools/feature_flags.py` | JSON-backed feature toggles with env var overrides |
| `tools/file_manager.py` | File hashing (SHA-256) and recursive extension search |

## Scripts

| Script | Purpose |
|---|---|
| `scripts/quality_gate.py` | Runs ruff format, lint, mypy, pytest, autodoc, markdownlint |
| `scripts/release.py` | Automates GitHub releases |
| `scripts/pre_commit.py` | Pre-commit hook runner |
| `scripts/autodoc.py` | Auto-generates documentation from source |
| `scripts/repo_cli.py` | Interactive CLI for common repo operations |

## CI Pipeline

Every push and PR triggers `.github/workflows/ci.yml`: Ruff (format + lint), Mypy (strict), Pytest (80% coverage), Markdownlint.

## License

Private sandbox — not intended for external use.

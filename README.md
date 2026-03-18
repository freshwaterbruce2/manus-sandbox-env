# Manus Sandbox Environment

AI agent sandbox for GitHub automation experiments. This repo is a testbed for building, validating, and iterating on Python-based GitHub automation tools — from CLI wrappers and quality gates to feature flags and file utilities.

## What's Here

```
manus-sandbox-env/
├── tools/             # Reusable Python modules (GitHub API, feature flags, file ops)
├── scripts/           # Automation runners (quality gate, release, pre-commit hooks)
├── experiments/       # Throwaway test scripts and AI agent experiments
├── tests/             # pytest suite for tools/ and scripts/
├── docs/              # Reports — testing results, compatibility, quality gate logs
├── .github/workflows/ # CI pipeline (lint, type-check, test, coverage)
├── pyproject.toml     # Ruff, mypy, pytest config
└── setup.sh           # One-shot environment bootstrap
```

## Quick Start

```bash
# Clone and bootstrap
git clone https://github.com/freshwaterbruce2/manus-sandbox-env.git
cd manus-sandbox-env
bash setup.sh

# Install dev dependencies
pip install ruff mypy pytest pytest-cov

# Run the quality gate (format → lint → type-check → test)
python scripts/quality_gate.py

# Use the GitHub helper
python -c "from tools.github_helper import GitHubHelper; h = GitHubHelper(); print(h.whoami())"
```

## Tools

| Module | Purpose |
|---|---|
| `tools/github_helper.py` | GitHub CLI wrapper — repos, issues, PRs, releases, branch ops |
| `tools/feature_flags.py` | JSON-backed feature toggles with env var overrides |
| `tools/file_manager.py` | File hashing (SHA-256) and recursive extension search |

## Scripts

| Script | Purpose |
|---|---|
| `scripts/quality_gate.py` | Runs ruff format → ruff lint → mypy → pytest → autodoc → markdownlint |
| `scripts/release.py` | Automates GitHub releases |
| `scripts/pre_commit.py` | Pre-commit hook runner |
| `scripts/autodoc.py` | Auto-generates documentation from source |
| `scripts/repo_cli.py` | Interactive CLI for common repo operations |

## CI Pipeline

Every push and PR triggers `.github/workflows/ci.yml`:

1. **Ruff** — format check + lint (rules: E, F, I, N, D)
2. **Mypy** — strict mode type checking
3. **Pytest** — full test suite with 80% coverage minimum
4. **Markdownlint** — docs hygiene

## Experiments

The `experiments/` folder is an AI agent test harness. Scripts there are intentionally rough — they exist to test cleanup tools, formatters, and automation pipelines against messy real-world input. See [`experiments/README.md`](experiments/README.md) for details.

## License

Private sandbox — not intended for external use.

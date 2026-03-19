# Manus Sandbox Environment

AI agent sandbox for GitHub automation experiments **plus** an automated testing system covering agent validation, API smoke tests, SQLite integrity checks, and build verification.

## What's Here

```text
manus-sandbox-env/
├── tools/                          # Reusable Python modules (GitHub API, feature flags, file ops)
├── scripts/                        # Automation runners
│   ├── quality_gate.py             # Format → lint → type-check → test
│   ├── run_tests.py                # ★ Test runner — orchestrates all 4 categories
│   ├── release.py                  # GitHub release automation
│   ├── pre_commit.py               # Pre-commit hook runner
│   ├── autodoc.py                  # Auto-generate docs from source
│   └── repo_cli.py                 # Interactive CLI for repo ops
├── tests/                          # pytest suite
│   ├── conftest.py                 # Shared fixtures and config loading
│   ├── test_agent_validation.py    # ★ Agent output validation
│   ├── test_api_smoke.py           # ★ API endpoint smoke tests
│   ├── test_sqlite_integrity.py    # ★ SQLite integrity checks
│   ├── test_build_verification.py  # ★ Build verification
│   ├── test_autodoc.py             # Autodoc tests
│   ├── test_feature_flags.py       # Feature flags tests
│   └── test_file_manager.py        # File manager tests
├── experiments/                    # AI agent experiment outputs
├── docs/                           # Reports and logs
├── test_config.yaml                # ★ Central config for all test categories
├── .github/workflows/ci.yml        # CI pipeline
├── pyproject.toml                  # Project config (ruff, mypy, pytest)
└── setup.sh                        # Environment bootstrap
```

## Automated Testing System

Four test categories run independently or together via the runner script.

### 1. Agent Output Validation

Validates AI agent outputs (DeepSeek, Kimi) dropped into `experiments/`. Checks include Python syntax validation via `ast.parse`, JSON schema checks, forbidden pattern detection (leaked API keys, secrets), file size limits, placeholder token detection, and empty file detection.

### 2. API Endpoint Smoke Tests

Automated smoke tests against Express backends (`localhost:5177`) and OpenRouter proxy (`localhost:3001`). Covers health checks, response shape validation, latency tracking, and timeout detection. Tests auto-skip when services aren't running.

### 3. SQLite Integrity Checks

Verifies SQLite databases at `D:\databases\` and `D:\learning-system\` aren't corrupted. Runs `PRAGMA integrity_check`, `PRAGMA foreign_key_check`, row count sanity checks, and schema validation. Unit tests always run against temp databases; live tests require Windows with D:\ drive.

### 4. Build Verification

Scripts that verify `pnpm` builds pass for specific apps in the monorepo at `C:\dev`. Checks exit codes, captures TypeScript errors, detects OOM, and reports pass/fail with timing. Live tests require Windows + pnpm + monorepo.

## Quick Start

```bash
# Clone and bootstrap
git clone https://github.com/freshwaterbruce2/manus-sandbox-env.git
cd manus-sandbox-env

# Install dependencies
pip install -e ".[dev]"

# Run ALL test categories
python scripts/run_tests.py

# Run a single category
python scripts/run_tests.py --category agent
python scripts/run_tests.py --category api
python scripts/run_tests.py --category sqlite
python scripts/run_tests.py --category build

# Verbose output
python scripts/run_tests.py --verbose

# CI mode (no color, machine-readable)
python scripts/run_tests.py --ci

# Run the full quality gate (format → lint → type-check → test)
python scripts/quality_gate.py

# Run pytest directly with coverage
pytest tests/ --cov=tools --cov=scripts --cov-report=term-missing
```

## Configuration

All test parameters live in `test_config.yaml` at the repo root. Edit this file to add endpoints, database paths, build targets, or adjust thresholds.

Key config sections:

- `agent_validation` — experiments directory, forbidden patterns, file size limits
- `api_smoke` — endpoint URLs, timeout, max latency
- `sqlite_integrity` — database paths, max row counts, integrity check toggles
- `build_verification` — monorepo root, app paths, build commands, timeouts

## Test Behavior

Tests are designed to be **portable**: unit tests always run (using mocked data and temp databases), while live integration tests auto-skip when the required environment isn't available (no Windows, no services running, no D:\ drive). This means CI on Ubuntu runs all unit tests, and local runs on Bruce's Windows machine additionally run live tests.

## Tools

| Module | Purpose |
|---|---|
| `tools/github_helper.py` | GitHub CLI wrapper — repos, issues, PRs, releases, branch ops |
| `tools/feature_flags.py` | JSON-backed feature toggles with env var overrides |
| `tools/file_manager.py` | File hashing (SHA-256) and recursive extension search |

## CI Pipeline

Every push and PR triggers `.github/workflows/ci.yml`:

1. **Ruff** — format check + lint
2. **Mypy** — strict mode type checking
3. **Pytest** — full test suite with 80% coverage minimum
4. **Markdownlint** — docs hygiene

## License

Private sandbox — not intended for external use.
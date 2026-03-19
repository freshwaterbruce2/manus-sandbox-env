# Manus Sandbox Environment

AI agent sandbox for GitHub automation experiments.

## Automated Testing System

The testing system validates the VibeTech monorepo infrastructure across four categories:

### Test Categories

**Agent Validation** (`tests/test_agent_validation.py`) — Validates AI-generated code outputs: Python/TypeScript/JSON syntax checking, JSON schema validation, cyclomatic complexity measurement, and placeholder text detection.

**API Smoke Tests** (`tests/test_api_smoke.py`) — Smoke tests for the Express backend (port 5177) and OpenRouter proxy (port 3001): health endpoints, response times, timeout handling. Skips gracefully if servers aren't running.

**SQLite Integrity** (`tests/test_sqlite_integrity.py`) — Database health checks: `PRAGMA integrity_check`, foreign key validation, schema snapshot comparison for drift detection, and row count sanity checks.

**Build Verification** (`tests/test_build_verification.py`) — Monorepo build validation: runs `pnpm build` on configured apps, `tsc --noEmit` type checking, and verifies no npm/yarn lockfiles have polluted the workspace.

### Configuration

All test parameters are defined in `config/test_config.yaml`: endpoint URLs, database paths, monorepo location, apps to verify, complexity thresholds, and placeholder patterns.

### Running Tests

```bash
# Install dev dependencies
pip install -e ".[dev]"

# Run all test categories with rich output
python run_tests.py --all

# Run specific categories
python run_tests.py --agent --api
python run_tests.py --sqlite --build

# Run directly with pytest
pytest tests/test_agent_validation.py -v
pytest tests/ -m "not requires_server" -v
```

### Test Markers

Tests use custom markers to control execution based on available infrastructure:

- `requires_server` — needs running backend/proxy servers
- `requires_db` — needs SQLite database access
- `requires_monorepo` — needs access to C:\dev monorepo

Skip markers automatically when infrastructure isn't available:
```bash
pytest tests/ -m "not requires_server and not requires_db" -v
```

## Development

```bash
# Setup
pip install -e ".[dev]"

# Lint & format
ruff check .
ruff format .

# Type check
mypy tools scripts
```

## License

MIT

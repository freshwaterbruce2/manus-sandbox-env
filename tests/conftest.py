"""Shared fixtures and configuration for the vibetech testing system."""

from __future__ import annotations

import os
import sqlite3
import tempfile
from pathlib import Path
from typing import Any, Generator

import pytest
import yaml


def _load_config() -> dict[str, Any]:
    """Load test_config.yaml from repo root."""
    config_path = Path(__file__).parent.parent / "test_config.yaml"
    if not config_path.exists():
        pytest.skip("test_config.yaml not found at repo root")
    with open(config_path, encoding="utf-8") as f:
        return yaml.safe_load(f)  # type: ignore[no-any-return]


@pytest.fixture(scope="session")
def test_config() -> dict[str, Any]:
    """Session-scoped fixture: parsed test_config.yaml."""
    return _load_config()


@pytest.fixture(scope="session")
def agent_config(test_config: dict[str, Any]) -> dict[str, Any]:
    """Agent validation config section."""
    return test_config.get("agent_validation", {})  # type: ignore[no-any-return]


@pytest.fixture(scope="session")
def api_config(test_config: dict[str, Any]) -> dict[str, Any]:
    """API smoke test config section."""
    return test_config.get("api_smoke", {})  # type: ignore[no-any-return]


@pytest.fixture(scope="session")
def sqlite_config(test_config: dict[str, Any]) -> dict[str, Any]:
    """SQLite integrity config section."""
    return test_config.get("sqlite_integrity", {})  # type: ignore[no-any-return]


@pytest.fixture(scope="session")
def build_config(test_config: dict[str, Any]) -> dict[str, Any]:
    """Build verification config section."""
    return test_config.get("build_verification", {})  # type: ignore[no-any-return]


@pytest.fixture(scope="session")
def experiments_dir() -> Path:
    """Path to experiments/ directory."""
    return Path(__file__).parent.parent / "experiments"


@pytest.fixture
def sample_sqlite_db() -> Generator[Path, None, None]:
    """Create a temporary SQLite database for testing the integrity checker itself."""
    with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as f:
        db_path = Path(f.name)

    conn = sqlite3.connect(str(db_path))
    cursor = conn.cursor()
    cursor.execute(
        "CREATE TABLE test_table (id INTEGER PRIMARY KEY, name TEXT NOT NULL, value REAL)"
    )
    cursor.execute(
        "CREATE TABLE related (id INTEGER PRIMARY KEY, test_id INTEGER, "
        "FOREIGN KEY (test_id) REFERENCES test_table(id))"
    )
    for i in range(100):
        cursor.execute(
            "INSERT INTO test_table (name, value) VALUES (?, ?)",
            (f"item_{i}", float(i) * 1.5),
        )
    for i in range(1, 51):
        cursor.execute("INSERT INTO related (test_id) VALUES (?)", (i,))
    conn.commit()
    conn.close()

    yield db_path

    db_path.unlink(missing_ok=True)


@pytest.fixture
def sample_experiment_dir() -> Generator[Path, None, None]:
    """Create a temp directory with sample agent output files for validation testing."""
    with tempfile.TemporaryDirectory() as tmpdir:
        d = Path(tmpdir)

        # Valid Python file
        (d / "valid_agent_output.py").write_text(
            'import json\n\ndef process():\n    return {"status": "ok"}\n',
            encoding="utf-8",
        )

        # Valid JSON file
        (d / "valid_output.json").write_text(
            '{"agent": "deepseek", "result": "success", "code": "print(1)"}',
            encoding="utf-8",
        )

        # Invalid Python (syntax error)
        (d / "broken_agent_output.py").write_text(
            "def broken(\n    return None\n",
            encoding="utf-8",
        )

        # File with forbidden pattern
        (d / "leaky_output.py").write_text(
            'API_KEY="sk-abc123"\ndef main():\n    pass\n',
            encoding="utf-8",
        )

        # Valid TypeScript-like file
        (d / "component.tsx").write_text(
            "export const App = () => { return <div>Hello</div>; };\n",
            encoding="utf-8",
        )

        yield d


def is_windows() -> bool:
    """Check if running on Windows."""
    return os.name == "nt"


def skip_unless_windows(reason: str = "Requires Windows environment") -> pytest.MarkDecorator:
    """Marker to skip tests that need Windows."""
    return pytest.mark.skipif(not is_windows(), reason=reason)


def skip_unless_service(
    host: str, port: int, reason: str = ""
) -> pytest.MarkDecorator:
    """Marker to skip tests when a network service is unavailable."""
    import socket

    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.settimeout(2)
    try:
        result = sock.connect_ex((host, port))
        available = result == 0
    except OSError:
        available = False
    finally:
        sock.close()

    skip_reason = reason or f"Service at {host}:{port} not available"
    return pytest.mark.skipif(not available, reason=skip_reason)
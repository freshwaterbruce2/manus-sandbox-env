"""Pytest fixtures and configuration for the automated testing system."""

from __future__ import annotations

import os
import sqlite3
from pathlib import Path
from typing import Any, Generator

import pytest
import yaml


def _find_config() -> Path:
    """Locate test_config.yaml relative to repo root."""
    here = Path(__file__).resolve().parent
    candidates = [
        here.parent / "config" / "test_config.yaml",
        here / "test_config.yaml",
        Path(os.environ.get("TEST_CONFIG", "")),
    ]
    for p in candidates:
        if p.exists():
            return p
    pytest.skip("test_config.yaml not found - set TEST_CONFIG env var")
    raise FileNotFoundError


@pytest.fixture(scope="session")
def config() -> dict[str, Any]:
    """Load and return the full test configuration dictionary."""
    cfg_path = _find_config()
    with open(cfg_path, encoding="utf-8") as fh:
        data: dict[str, Any] = yaml.safe_load(fh)
    return data


@pytest.fixture(scope="session")
def api_config(config: dict[str, Any]) -> dict[str, Any]:
    """Return just the api section of config."""
    return config.get("api", {})


@pytest.fixture(scope="session")
def db_config(config: dict[str, Any]) -> dict[str, Any]:
    """Return just the databases section of config."""
    return config.get("databases", {})


@pytest.fixture(scope="session")
def monorepo_config(config: dict[str, Any]) -> dict[str, Any]:
    """Return just the monorepo section of config."""
    return config.get("monorepo", {})


@pytest.fixture(scope="session")
def agent_config(config: dict[str, Any]) -> dict[str, Any]:
    """Return just the agent_validation section of config."""
    return config.get("agent_validation", {})


@pytest.fixture()
def temp_sqlite(tmp_path: Path) -> Generator[Path, None, None]:
    """Create a temporary SQLite database for testing."""
    db_path = tmp_path / "test.db"
    conn = sqlite3.connect(str(db_path))
    conn.execute("CREATE TABLE test_table (id INTEGER PRIMARY KEY, name TEXT)")
    conn.execute("INSERT INTO test_table VALUES (1, 'test')")
    conn.commit()
    conn.close()
    yield db_path

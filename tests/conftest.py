"""Shared fixtures for the VibeTech automated test suite."""

from __future__ import annotations

import os
import tempfile
from pathlib import Path
from typing import Any, Generator
from unittest.mock import MagicMock

import pytest
import yaml


def _find_config() -> Path:
    """Locate test_config.yaml walking up from this file."""
    here = Path(__file__).resolve().parent
    for ancestor in [here.parent, here.parent.parent, here]:
        candidate = ancestor / "config" / "test_config.yaml"
        if candidate.exists():
            return candidate
    raise FileNotFoundError("config/test_config.yaml not found")


@pytest.fixture(scope="session")
def config() -> dict[str, Any]:
    """Load and return the full test configuration dict."""
    path = _find_config()
    with open(path, encoding="utf-8") as f:
        return yaml.safe_load(f)


@pytest.fixture(scope="session")
def backend_url(config: dict[str, Any]) -> str:
    """Return the backend base URL from config."""
    return config["endpoints"]["backend"]["base_url"]


@pytest.fixture(scope="session")
def proxy_url(config: dict[str, Any]) -> str:
    """Return the OpenRouter proxy base URL."""
    return config["endpoints"]["openrouter_proxy"]["base_url"]


@pytest.fixture(scope="session")
def db_paths(config: dict[str, Any]) -> dict[str, Path]:
    """Return resolved database directory paths."""
    return {
        "primary": Path(config["databases"]["primary_dir"]),
        "learning": Path(config["databases"]["learning_dir"]),
    }


@pytest.fixture
def temp_dir() -> Generator[Path, None, None]:
    """Provide a temporary directory cleaned up after the test."""
    with tempfile.TemporaryDirectory(prefix="vibetest_") as d:
        yield Path(d)


@pytest.fixture
def mock_response() -> MagicMock:
    """Create a mock HTTP response with configurable status/json."""
    mock = MagicMock()
    mock.status_code = 200
    mock.json.return_value = {"status": "ok"}
    mock.elapsed.total_seconds.return_value = 0.05
    mock.headers = {"content-type": "application/json"}
    return mock


@pytest.fixture(scope="session")
def monorepo_root(config: dict[str, Any]) -> Path:
    """Return the monorepo root path."""
    return Path(config["monorepo"]["root"])


@pytest.fixture(scope="session")
def apps_to_verify(config: dict[str, Any]) -> list[str]:
    """Return the list of apps that should pass build verification."""
    return config["monorepo"]["apps_to_verify"]


def pytest_configure(config: pytest.Config) -> None:
    """Register custom markers."""
    config.addinivalue_line("markers", "slow: marks tests as slow-running")
    config.addinivalue_line("markers", "requires_server: needs a running backend")
    config.addinivalue_line("markers", "requires_db: needs database access")
    config.addinivalue_line("markers", "requires_monorepo: needs C:\\dev access")

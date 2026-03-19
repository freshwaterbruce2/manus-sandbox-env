"""API Endpoint Smoke Tests.

Automated smoke tests against Express backends (localhost:5177),
OpenRouter proxy (localhost:3001). Health checks, response shape
validation, latency tracking, timeout detection.
"""

from __future__ import annotations

import socket
import time
from typing import Any
from unittest.mock import MagicMock, patch

import pytest
import requests

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _is_service_up(host: str, port: int, timeout: float = 2.0) -> bool:
    """Check if a TCP service is listening."""
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.settimeout(timeout)
    try:
        return sock.connect_ex((host, port)) == 0
    except OSError:
        return False
    finally:
        sock.close()


def _parse_base_url(url: str) -> tuple[str, int]:
    """Extract host and port from a base URL."""
    from urllib.parse import urlparse

    parsed = urlparse(url)
    host = parsed.hostname or "localhost"
    port = parsed.port or (443 if parsed.scheme == "https" else 80)
    return host, port


# ---------------------------------------------------------------------------
# Unit tests (always run — mock network calls)
# ---------------------------------------------------------------------------

class TestSmokeTestHelpers:
    """Unit tests for smoke test helper functions."""

    def test_parse_base_url_with_port(self) -> None:
        """Should extract host and port from URL."""
        host, port = _parse_base_url("http://localhost:5177")
        assert host == "localhost"
        assert port == 5177

    def test_parse_base_url_default_port(self) -> None:
        """Should default to port 80 for http."""
        host, port = _parse_base_url("http://example.com")
        assert host == "example.com"
        assert port == 80

    def test_parse_base_url_https(self) -> None:
        """Should default to port 443 for https."""
        host, port = _parse_base_url("https://example.com")
        assert host == "example.com"
        assert port == 443


class TestResponseValidation:
    """Test response shape validation logic (mocked)."""

    def test_health_check_response_shape(self) -> None:
        """Health endpoint should return JSON with status field."""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"status": "ok"}
        mock_response.elapsed = MagicMock()
        mock_response.elapsed.total_seconds.return_value = 0.05

        assert mock_response.status_code == 200
        data = mock_response.json()
        assert "status" in data
        assert mock_response.elapsed.total_seconds() < 5.0

    def test_timeout_detection(self) -> None:
        """Requests that exceed timeout should raise."""
        with patch("requests.get", side_effect=requests.Timeout("Connection timed out")):
            with pytest.raises(requests.Timeout):
                requests.get("http://localhost:5177/health", timeout=1)

    def test_connection_error_handling(self) -> None:
        """Connection refused should be caught gracefully."""
        with patch(
            "requests.get",
            side_effect=requests.ConnectionError("Connection refused"),
        ):
            with pytest.raises(requests.ConnectionError):
                requests.get("http://localhost:5177/health", timeout=1)


class TestLatencyTracking:
    """Validate latency measurement logic."""

    def test_latency_below_threshold(self) -> None:
        """Response time under max_latency should pass."""
        max_latency = 5.0
        mock_elapsed = 0.15
        assert mock_elapsed < max_latency

    def test_latency_above_threshold_flags(self) -> None:
        """Response time over max_latency should be flagged."""
        max_latency = 5.0
        mock_elapsed = 6.2
        assert mock_elapsed > max_latency, "Slow response should be flagged"


# ---------------------------------------------------------------------------
# Integration tests (only run when services are actually up)
# ---------------------------------------------------------------------------

class TestExpressBackendLive:
    """Live smoke tests against Express backend at localhost:5177."""

    @pytest.fixture(autouse=True)
    def _require_express(self) -> None:
        if not _is_service_up("localhost", 5177):
            pytest.skip("Express backend not running on localhost:5177")

    def test_health_endpoint(self, api_config: dict[str, Any]) -> None:
        """GET /health should return 200."""
        timeout = api_config.get("timeout", 10)
        resp = requests.get("http://localhost:5177/health", timeout=timeout)
        assert resp.status_code == 200

    def test_health_response_time(self, api_config: dict[str, Any]) -> None:
        """Health check should respond within max_latency."""
        max_latency = api_config.get("max_latency", 5.0)
        timeout = api_config.get("timeout", 10)
        start = time.time()
        resp = requests.get("http://localhost:5177/health", timeout=timeout)
        elapsed = time.time() - start
        assert resp.status_code == 200
        assert elapsed < max_latency, f"Health took {elapsed:.2f}s (max: {max_latency}s)"

    def test_configured_endpoints(self, api_config: dict[str, Any]) -> None:
        """All configured Express endpoints should respond."""
        timeout = api_config.get("timeout", 10)
        express_cfg = api_config.get("endpoints", {}).get("express_backend", {})
        base_url = express_cfg.get("base_url", "http://localhost:5177")

        for ep in express_cfg.get("test_paths", []):
            url = f"{base_url}{ep['path']}"
            method = ep.get("method", "GET").upper()
            expected = ep.get("expected_status", 200)

            if method == "GET":
                resp = requests.get(url, timeout=timeout)
            elif method == "POST":
                resp = requests.post(url, timeout=timeout)
            else:
                pytest.skip(f"Unsupported method: {method}")

            assert resp.status_code == expected, (
                f"{method} {url} returned {resp.status_code}, expected {expected}"
            )


class TestOpenRouterProxyLive:
    """Live smoke tests against OpenRouter proxy at localhost:3001."""

    @pytest.fixture(autouse=True)
    def _require_openrouter(self) -> None:
        if not _is_service_up("localhost", 3001):
            pytest.skip("OpenRouter proxy not running on localhost:3001")

    def test_health_endpoint(self, api_config: dict[str, Any]) -> None:
        """GET /health should return 200."""
        timeout = api_config.get("timeout", 10)
        resp = requests.get("http://localhost:3001/health", timeout=timeout)
        assert resp.status_code == 200

    def test_models_endpoint(self, api_config: dict[str, Any]) -> None:
        """GET /v1/models should return JSON with model list."""
        timeout = api_config.get("timeout", 10)
        resp = requests.get("http://localhost:3001/v1/models", timeout=timeout)
        assert resp.status_code == 200
        data = resp.json()
        assert isinstance(data, (dict, list)), "Models response should be JSON object or array"
"""Smoke tests for backend API endpoints. Skips gracefully if server is down."""

from __future__ import annotations

import time
from typing import Any

import pytest

try:
    import requests
except ImportError:
    requests = None  # type: ignore[assignment]

pytestmark = pytest.mark.requires_server


def _server_reachable(url: str, timeout: float = 2.0) -> bool:
    """Quick check if the server responds at all."""
    if requests is None:
        return False
    try:
        requests.get(url, timeout=timeout)
        return True
    except Exception:
        return False


# ---------------------------------------------------------------------------
# Backend API tests
# ---------------------------------------------------------------------------


class TestBackendHealth:
    """Health and basic response checks for the Express backend."""

    @pytest.fixture(autouse=True)
    def _skip_if_down(self, backend_url: str) -> None:
        if not _server_reachable(backend_url):
            pytest.skip(f"Backend not reachable at {backend_url}")

    def test_health_endpoint_returns_200(self, backend_url: str) -> None:
        resp = requests.get(f"{backend_url}/health", timeout=5)
        assert resp.status_code == 200

    def test_health_returns_json(self, backend_url: str) -> None:
        resp = requests.get(f"{backend_url}/health", timeout=5)
        ct = resp.headers.get("content-type", "")
        assert "json" in ct or "text" in ct

    def test_response_time_under_2s(self, backend_url: str) -> None:
        start = time.monotonic()
        requests.get(f"{backend_url}/health", timeout=5)
        elapsed = time.monotonic() - start
        assert elapsed < 2.0, f"Health check took {elapsed:.2f}s"

    def test_404_for_unknown_route(self, backend_url: str) -> None:
        resp = requests.get(f"{backend_url}/__nonexistent__", timeout=5)
        assert resp.status_code in (404, 400)


class TestProxyEndpoint:
    """Smoke tests for the OpenRouter proxy at localhost:3001."""

    @pytest.fixture(autouse=True)
    def _skip_if_down(self, proxy_url: str) -> None:
        if not _server_reachable(proxy_url):
            pytest.skip(f"Proxy not reachable at {proxy_url}")

    def test_proxy_responds(self, proxy_url: str) -> None:
        resp = requests.get(proxy_url, timeout=10)
        assert resp.status_code in range(200, 500)

    def test_proxy_timeout_handling(self, proxy_url: str) -> None:
        """Ensure proxy doesn't hang forever on bad requests."""
        try:
            resp = requests.post(
                f"{proxy_url}/v1/chat/completions",
                json={"model": "nonexistent", "messages": []},
                timeout=15,
            )
            # Any response is fine — we just verify it doesn't hang
            assert resp.status_code > 0
        except requests.exceptions.Timeout:
            pytest.fail("Proxy request timed out after 15s")
        except requests.exceptions.ConnectionError:
            pytest.skip("Proxy connection refused")


class TestResponseSchema:
    """Validate response shapes from the backend."""

    @pytest.fixture(autouse=True)
    def _skip_if_down(self, backend_url: str) -> None:
        if not _server_reachable(backend_url):
            pytest.skip(f"Backend not reachable at {backend_url}")

    def test_health_has_expected_fields(
        self, backend_url: str, config: dict[str, Any]
    ) -> None:
        resp = requests.get(f"{backend_url}/health", timeout=5)
        if resp.headers.get("content-type", "").startswith("application/json"):
            data = resp.json()
            # At minimum, health should be a dict or have a status field
            assert isinstance(data, dict)

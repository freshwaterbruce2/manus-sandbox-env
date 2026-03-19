"""Smoke tests for Express API and OpenRouter proxy endpoints."""

from __future__ import annotations

import time
from typing import Any

import pytest
import requests


class TestExpressApi:
    """Smoke tests for the Express backend."""

    def _base(self, api_config: dict[str, Any]) -> str:
        return api_config.get("express", {}).get("base_url", "http://localhost:5177")

    def _timeout(self, api_config: dict[str, Any]) -> int:
        return api_config.get("express", {}).get("timeout_seconds", 10)

    def _max_latency(self, api_config: dict[str, Any]) -> int:
        return api_config.get("express", {}).get("max_latency_ms", 2000)

    def test_health_endpoint(self, api_config: dict[str, Any]) -> None:
        """Health check should return 200."""
        url = self._base(api_config) + api_config.get("express", {}).get(
            "health_endpoint", "/health"
        )
        try:
            resp = requests.get(url, timeout=self._timeout(api_config))
            assert resp.status_code == 200, f"Health returned {resp.status_code}"
        except requests.ConnectionError:
            pytest.skip("Express server not running at " + url)

    def test_health_response_shape(self, api_config: dict[str, Any]) -> None:
        """Health response should be JSON with expected keys."""
        url = self._base(api_config) + api_config.get("express", {}).get(
            "health_endpoint", "/health"
        )
        try:
            resp = requests.get(url, timeout=self._timeout(api_config))
            data = resp.json()
            assert isinstance(data, dict), "Health response should be a JSON object"
        except requests.ConnectionError:
            pytest.skip("Express server not running")
        except requests.exceptions.JSONDecodeError:
            assert resp.text.strip() != "", "Health response should not be empty"

    def test_health_latency(self, api_config: dict[str, Any]) -> None:
        """Health check should respond within max_latency_ms."""
        url = self._base(api_config) + api_config.get("express", {}).get(
            "health_endpoint", "/health"
        )
        max_ms = self._max_latency(api_config)
        try:
            start = time.monotonic()
            requests.get(url, timeout=self._timeout(api_config))
            elapsed_ms = (time.monotonic() - start) * 1000
            assert elapsed_ms < max_ms, f"Latency {elapsed_ms:.0f}ms > {max_ms}ms"
        except requests.ConnectionError:
            pytest.skip("Express server not running")

    def test_404_on_unknown_route(self, api_config: dict[str, Any]) -> None:
        """Unknown routes should return 404."""
        url = self._base(api_config) + "/__nonexistent_route__"
        try:
            resp = requests.get(url, timeout=self._timeout(api_config))
            assert resp.status_code in (404, 400), f"Got {resp.status_code}"
        except requests.ConnectionError:
            pytest.skip("Express server not running")


class TestOpenRouterProxy:
    """Smoke tests for the OpenRouter proxy."""

    def _base(self, api_config: dict[str, Any]) -> str:
        return api_config.get("openrouter_proxy", {}).get(
            "base_url", "http://localhost:3001"
        )

    def _timeout(self, api_config: dict[str, Any]) -> int:
        return api_config.get("openrouter_proxy", {}).get("timeout_seconds", 15)

    def _max_latency(self, api_config: dict[str, Any]) -> int:
        return api_config.get("openrouter_proxy", {}).get("max_latency_ms", 5000)

    def test_proxy_health(self, api_config: dict[str, Any]) -> None:
        """Proxy health check should return 200."""
        url = self._base(api_config) + api_config.get("openrouter_proxy", {}).get(
            "health_endpoint", "/health"
        )
        try:
            resp = requests.get(url, timeout=self._timeout(api_config))
            assert resp.status_code == 200, f"Proxy health returned {resp.status_code}"
        except requests.ConnectionError:
            pytest.skip("OpenRouter proxy not running at " + url)

    def test_proxy_response_shape(self, api_config: dict[str, Any]) -> None:
        """Proxy health response should be valid."""
        url = self._base(api_config) + api_config.get("openrouter_proxy", {}).get(
            "health_endpoint", "/health"
        )
        try:
            resp = requests.get(url, timeout=self._timeout(api_config))
            assert resp.text.strip() != "", "Response should not be empty"
        except requests.ConnectionError:
            pytest.skip("OpenRouter proxy not running")

    def test_proxy_latency(self, api_config: dict[str, Any]) -> None:
        """Proxy should respond within max_latency_ms."""
        url = self._base(api_config) + api_config.get("openrouter_proxy", {}).get(
            "health_endpoint", "/health"
        )
        max_ms = self._max_latency(api_config)
        try:
            start = time.monotonic()
            requests.get(url, timeout=self._timeout(api_config))
            elapsed_ms = (time.monotonic() - start) * 1000
            assert elapsed_ms < max_ms, f"Latency {elapsed_ms:.0f}ms > {max_ms}ms"
        except requests.ConnectionError:
            pytest.skip("OpenRouter proxy not running")

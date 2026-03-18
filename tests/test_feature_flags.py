"""Tests for the feature_flags utility."""

import json
import os
from pathlib import Path
from typing import Generator

import pytest

from tools.feature_flags import FeatureFlags


@pytest.fixture
def temp_config(tmp_path: Path) -> Generator[Path, None, None]:
    """Create a temporary feature flags config file."""
    config_file = tmp_path / "test_flags.json"
    flags = {"existing_feature": True, "disabled_feature": False}
    with open(config_file, "w") as f:
        json.dump(flags, f)
    yield config_file


def test_load_flags(temp_config: Path) -> None:
    """Test loading flags from a config file."""
    ff = FeatureFlags(str(temp_config))
    assert ff.is_enabled("existing_feature") is True
    assert ff.is_enabled("disabled_feature") is False
    assert ff.is_enabled("non_existent", default=True) is True


def test_env_override(temp_config: Path) -> None:
    """Test environment variable override for feature flags."""
    ff = FeatureFlags(str(temp_config))
    os.environ["MANUS_DISABLED_FEATURE"] = "true"
    try:
        assert ff.is_enabled("disabled_feature") is True
    finally:
        del os.environ["MANUS_DISABLED_FEATURE"]


def test_set_flag(tmp_path: Path) -> None:
    """Test setting and saving a feature flag."""
    config_file = tmp_path / "new_flags.json"
    ff = FeatureFlags(str(config_file))
    ff.set_flag("new_feature", True)

    # Verify in memory
    assert ff.is_enabled("new_feature") is True

    # Verify on disk
    with open(config_file, "r") as f:
        data = json.load(f)
        assert data["new_feature"] is True


def test_invalid_config(tmp_path: Path) -> None:
    """Test handling of invalid JSON config."""
    config_file = tmp_path / "invalid.json"
    with open(config_file, "w") as f:
        f.write("invalid json")

    ff = FeatureFlags(str(config_file))
    assert ff.flags == {}

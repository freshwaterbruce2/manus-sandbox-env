"""feature_flags.py — Lightweight Feature Flag utility for the Manus sandbox.

Provides a simple way to enable or disable features based on a configuration file.
This allows for safer deployments and experimental feature testing.
"""

import json
import os
from pathlib import Path
from typing import Dict


class FeatureFlags:
    """Manages feature flags using a JSON configuration file."""

    def __init__(self, config_path: str = "feature_flags.json") -> None:
        """Initialize the feature flags manager.

        Args:
            config_path: Path to the JSON configuration file.

        """
        self.config_path = Path(config_path)
        self.flags: Dict[str, bool] = self._load_flags()

    def _load_flags(self) -> Dict[str, bool]:
        """Load flags from the config file or return defaults."""
        if not self.config_path.exists():
            return {}
        try:
            with open(self.config_path, "r") as f:
                data = json.load(f)
                if isinstance(data, dict):
                    return {str(k): bool(v) for k, v in data.items()}
        except (json.JSONDecodeError, OSError):
            pass
        return {}

    def is_enabled(self, feature_name: str, default: bool = False) -> bool:
        """Check if a feature is enabled.

        Args:
            feature_name: The name of the feature to check.
            default: The default value if the feature is not found.

        Returns:
            True if the feature is enabled, False otherwise.

        """
        # Allow environment variable override: MANUS_FEATURE_NAME=true/false
        env_var = f"MANUS_{feature_name.upper()}"
        env_val = os.environ.get(env_var)
        if env_val is not None:
            return env_val.lower() in ("true", "1", "yes")

        return self.flags.get(feature_name, default)

    def set_flag(self, feature_name: str, enabled: bool) -> None:
        """Set a feature flag and save to the config file.

        Args:
            feature_name: The name of the feature.
            enabled: Whether the feature should be enabled.

        """
        self.flags[feature_name] = enabled
        with open(self.config_path, "w") as f:
            json.dump(self.flags, f, indent=2)


# Global instance for easy access
_manager = FeatureFlags()


def is_enabled(feature_name: str, default: bool = False) -> bool:
    """Global helper to check if a feature is enabled."""
    return _manager.is_enabled(feature_name, default)


if __name__ == "__main__":
    # Demo usage
    print("=== Feature Flag Demo ===")
    test_feature = "new_analytics_engine"

    # Check initial state
    print(f"Feature '{test_feature}' enabled: {is_enabled(test_feature)}")

    # Set and check
    print(f"Enabling '{test_feature}'...")
    _manager.set_flag(test_feature, True)
    print(f"Feature '{test_feature}' enabled: {is_enabled(test_feature)}")

    # Clean up demo file
    if _manager.config_path.exists():
        _manager.config_path.unlink()

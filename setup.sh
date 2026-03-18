#!/bin/bash
# setup.sh — Universal Environment Setup for the Sandbox Repository
#
# This script configures the environment for any AI agent or developer.
# It installs necessary dependencies and sets up local Git hooks.

set -e

echo "--- Initializing Sandbox Environment ---"

# 1. Install Python dependencies
echo "Installing Python dependencies (ruff, mypy, pytest, pytest-cov)..."
pip install --upgrade pip
pip install ruff mypy pytest pytest-cov

# 2. Install Node.js dependencies (for markdownlint)
if command -v npm &> /dev/null; then
    echo "Installing markdownlint-cli via npm..."
    npm install -g markdownlint-cli || echo "Warning: Failed to install markdownlint-cli globally. Try installing it manually."
elif command -v pnpm &> /dev/null; then
    echo "Installing markdownlint-cli via pnpm..."
    pnpm add -g markdownlint-cli
else
    echo "Warning: Node.js/npm not found. Markdown linting will be skipped."
fi

# 3. Setup Git hooks
if [ -d ".git" ]; then
    echo "Setting up local Git hooks..."
    python3 scripts/setup_hooks.py
else
    echo "Warning: .git directory not found. Skipping hook installation."
fi

# 4. Final Verification
echo "Verifying installation..."
python3 scripts/repo_cli.py check || echo "Warning: Quality Gate failed. Please fix issues before contributing."

echo "--- Setup Complete! ---"
echo "You can now use './scripts/repo_cli.py' or alias it to 'm' for repository tasks."

# Contributing to the Sandbox Repository

Welcome to the sandbox repository! This guide outlines the standards and processes for contributing to this project, ensuring that all contributions maintain the highest level of quality and consistency. Whether you are a human developer or an AI agent, adhering to these guidelines is crucial for a smooth and efficient workflow.

## 1. Setting Up Your Environment

To get started, clone the repository and run the `setup.sh` script. This script will install all necessary Python and Node.js dependencies (Ruff, Mypy, Pytest, markdownlint-CLI) and configure your local Git hooks.

```bash
git clone <repository-url>
cd <repository-name>
./setup.sh
```

## 2. The Repository CLI (`repo_cli.py`)

All common repository tasks are managed through the `scripts/repo_cli.py` script. You can execute it directly or create a shell alias for convenience (e.g., `alias m='./scripts/repo_cli.py'` in your `.bashrc` or `.zshrc`).

Key commands include:

- **`./scripts/repo_cli.py check`:** Runs the full Quality Gate, performing all checks (formatting, linting, type checking, testing, auto-documentation, Markdown linting).
- **`./scripts/repo_cli.py test`:** Executes the unit test suite.
- **`./scripts/repo_cli.py doc`:** Regenerates the `LIBRARY.md` documentation.
- **`./scripts/repo_cli.py release [major|minor|patch|show]`:** Manages semantic versioning and Git tags.
- **`./scripts/repo_cli.py info`:** Displays system and repository environment information.

## 3. The Quality Gate

This repository enforces a strict **Quality Gate** to ensure code quality and maintainability. The `scripts/quality_gate.py` script performs the following checks:

- **Python Formatting (Ruff):** Ensures all Python code adheres to a consistent style.
- **Python Linting (Ruff):** Identifies potential errors, stylistic issues, and bad practices in Python code.
- **Static Type Checking (Mypy):** Verifies type hints in Python code to catch type-related bugs early.
- **Automated Unit Testing (Pytest):** Runs comprehensive unit tests to ensure functional correctness. All tests must pass.
- **Auto-Documentation Generation (`autodoc.py`):** Automatically generates and updates `LIBRARY.md` from Python docstrings.
- **Markdown Linting (`markdownlint-cli`):** Ensures all Markdown files (including `README.md`, `CONTRIBUTING.md`, and `LIBRARY.md`) follow consistent formatting and style guidelines.

**All checks must pass for a contribution to be accepted.**

## 4. Git Pre-commit Hooks

To prevent non-compliant code from ever being committed, a Git pre-commit hook is installed by `setup.sh`. This hook automatically runs the full Quality Gate before each commit. If any check fails, the commit will be aborted, and you will be prompted to fix the issues.

This ensures that your local commits are always clean and ready for integration.

## 5. Contribution Guidelines

- **Branching:** Always create a new branch for your features or bug fixes (e.g., `feature/my-new-feature`, `bugfix/issue-123`).
- **Commits:** Write clear, concise commit messages that explain the purpose of your changes. Follow [Conventional Commits](https://www.conventionalcommits.org/en/v1.0.0/) guidelines (e.g., `feat: add new feature`, `fix: resolve bug`).
- **Code Quality:** Ensure your code is well-documented with docstrings, type hints, and adheres to the formatting and linting rules enforced by the Quality Gate.
- **Testing:** Write unit tests for new functionality and ensure all existing tests pass. Aim for high code coverage.
- **Documentation:** Update `LIBRARY.md` (via `repo_cli.py doc`) and any other relevant documentation (like this `CONTRIBUTING.md`) as part of your changes.
- **Pull Requests:** Once your changes are complete and all Quality Gate checks pass, open a Pull Request to the `main` branch. Provide a clear description of your changes and reference any related issues.

By following these guidelines, you help maintain a high-quality, reliable, and easy-to-understand codebase for everyone.

## References

[1] Git Hooks: Customizing Git. [https://git-scm.com/book/en/v2/Customizing-Git-Git-Hooks](https://git-scm.com/book/en/v2/Customizing-Git-Git-Hooks)
[2] Conventional Commits. [https://www.conventionalcommits.org/en/v1.0.0/](https://www.conventionalcommits.org/en/v1.0.0/)
[3] Ruff: An extremely fast Python linter and formatter, written in Rust. [https://docs.astral.sh/ruff/](https://docs.astral.sh/ruff/)
[4] Mypy: Optional Static Typing for Python. [https://mypy-lang.org/](https://mypy-lang.org/)
[5] pytest: The pytest testing framework. [https://docs.pytest.org/](https://docs.pytest.org/)
[6] markdownlint-CLI: A Node.js command-line interface for markdownlint. [https://github.com/igorshubovych/markdownlint-cli](https://github.com/igorshubovych/markdownlint-cli)

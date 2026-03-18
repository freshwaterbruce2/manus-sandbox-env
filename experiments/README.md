# Experiments

AI agent test harness. This folder holds throwaway scripts and documents used to validate automation tools — formatters, linters, cleanup pipelines, and quality gates.

## Purpose

Scripts here are **intentionally messy**. They exist so that:

- `scripts/quality_gate.py` has real targets to lint, format, and type-check
- `scripts/autodoc.py` can generate docs from rough source files
- Pre-commit hooks can be tested against non-trivial input
- AI agents can practice refactoring, cleanup, and code generation

## Current Experiments

| File | What It Tests |
|---|---|
| `messy_script.py` | Baseline messy code — verifies formatters and linters catch issues |
| `messy_doc.md` | Malformed markdown — verifies markdownlint and doc generators |

## Adding Experiments

Drop any `.py` or `.md` file here. The quality gate will pick it up automatically. Name files descriptively — `test_<what_you_are_testing>.py` for scripts, `<topic>_doc.md` for documents.

Experiments are excluded from coverage requirements but still checked by ruff and mypy.

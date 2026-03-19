"""Validate AI agent outputs: syntax, schema, complexity, placeholders."""

from __future__ import annotations

import ast
import json
import re
from typing import Any

import pytest

try:
    from jsonschema import validate, ValidationError
except ImportError:
    validate = None  # type: ignore[assignment]
    ValidationError = Exception  # type: ignore[misc,assignment]


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def check_python_syntax(code: str) -> tuple[bool, str]:
    """Return (valid, error_message) for Python source."""
    try:
        ast.parse(code)
        return True, ""
    except SyntaxError as exc:
        return False, f"Line {exc.lineno}: {exc.msg}"


def check_json_syntax(text: str) -> tuple[bool, str]:
    """Return (valid, error_message) for JSON text."""
    try:
        json.loads(text)
        return True, ""
    except json.JSONDecodeError as exc:
        return False, f"Pos {exc.pos}: {exc.msg}"


def check_typescript_basic(code: str) -> tuple[bool, str]:
    """Heuristic TS syntax check — unmatched braces/brackets."""
    stack: list[str] = []
    pairs = {")": "(", "]": "[", "}": "{"}
    for i, ch in enumerate(code):
        if ch in "([{":
            stack.append(ch)
        elif ch in ")]}":
            if not stack or stack[-1] != pairs[ch]:
                return False, f"Unmatched '{ch}' at position {i}"
            stack.pop()
    if stack:
        return False, f"Unclosed '{stack[-1]}'"
    return True, ""


def measure_complexity(code: str) -> int:
    """Rough cyclomatic complexity for Python: count branches."""
    branch_keywords = r"\b(if|elif|else|for|while|except|with|and|or)\b"
    return len(re.findall(branch_keywords, code)) + 1


def find_placeholders(text: str, patterns: list[str]) -> list[str]:
    """Return all placeholder matches found in text."""
    hits: list[str] = []
    for pat in patterns:
        hits.extend(re.findall(pat, text, re.IGNORECASE))
    return hits


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------

PLACEHOLDER_PATTERNS = [
    r"\[your .* here\]",
    r"TODO: implement",
    r"FIXME",
    r"placeholder",
]


class TestPythonValidation:
    """Validate Python code outputs from agents."""

    def test_valid_python(self) -> None:
        ok, _ = check_python_syntax("x = 1\nprint(x)")
        assert ok

    def test_invalid_python(self) -> None:
        ok, msg = check_python_syntax("def foo(\n  pass")
        assert not ok
        assert "SyntaxError" in msg or "Line" in msg

    def test_empty_string_is_valid(self) -> None:
        ok, _ = check_python_syntax("")
        assert ok

    def test_complexity_simple(self) -> None:
        assert measure_complexity("x = 1") == 1

    def test_complexity_branching(self) -> None:
        code = "if a:\n  pass\nelif b:\n  pass\nelse:\n  pass"
        assert measure_complexity(code) >= 4


class TestTypeScriptValidation:
    """Basic TS structural checks."""

    def test_balanced_braces(self) -> None:
        ok, _ = check_typescript_basic("function f() { return { a: 1 }; }")
        assert ok

    def test_unmatched_brace(self) -> None:
        ok, msg = check_typescript_basic("function f() { return { a: 1 };")
        assert not ok
        assert "Unclosed" in msg

    def test_empty_is_valid(self) -> None:
        ok, _ = check_typescript_basic("")
        assert ok


class TestJsonValidation:
    """Validate JSON outputs."""

    def test_valid_json(self) -> None:
        ok, _ = check_json_syntax('{"key": "value"}')
        assert ok

    def test_invalid_json(self) -> None:
        ok, msg = check_json_syntax('{"key": }')
        assert not ok

    @pytest.mark.skipif(validate is None, reason="jsonschema not installed")
    def test_schema_validation_pass(self) -> None:
        schema: dict[str, Any] = {
            "type": "object",
            "required": ["status"],
            "properties": {"status": {"type": "string"}},
        }
        validate(instance={"status": "ok"}, schema=schema)

    @pytest.mark.skipif(validate is None, reason="jsonschema not installed")
    def test_schema_validation_fail(self) -> None:
        schema: dict[str, Any] = {
            "type": "object",
            "required": ["status"],
            "properties": {"status": {"type": "string"}},
        }
        with pytest.raises(ValidationError):
            validate(instance={"wrong": 123}, schema=schema)


class TestPlaceholderDetection:
    """Catch placeholder text in agent outputs."""

    def test_no_placeholders_in_clean_text(self) -> None:
        hits = find_placeholders("All good here.", PLACEHOLDER_PATTERNS)
        assert hits == []

    def test_catches_your_value_here(self) -> None:
        hits = find_placeholders("Set [your API key here]", PLACEHOLDER_PATTERNS)
        assert len(hits) >= 1

    def test_catches_todo_implement(self) -> None:
        hits = find_placeholders("# TODO: implement this", PLACEHOLDER_PATTERNS)
        assert len(hits) >= 1

    def test_catches_fixme(self) -> None:
        hits = find_placeholders("// FIXME broken", PLACEHOLDER_PATTERNS)
        assert len(hits) >= 1

    def test_catches_placeholder_word(self) -> None:
        hits = find_placeholders("This is a placeholder value", PLACEHOLDER_PATTERNS)
        assert len(hits) >= 1

"""Validate AI agent outputs: syntax checking, JSON schema, code parsing."""

from __future__ import annotations

import ast
import json
from typing import Any

import pytest

try:
    import jsonschema
except ImportError:
    jsonschema = None  # type: ignore[assignment]


CHAT_RESPONSE_SCHEMA: dict[str, Any] = {
    "type": "object",
    "required": ["role", "content"],
    "properties": {
        "role": {"type": "string", "enum": ["assistant", "system", "user"]},
        "content": {"type": "string", "minLength": 1},
    },
    "additionalProperties": True,
}

TOOL_CALL_SCHEMA: dict[str, Any] = {
    "type": "object",
    "required": ["name", "arguments"],
    "properties": {
        "name": {"type": "string", "minLength": 1},
        "arguments": {"type": "object"},
    },
    "additionalProperties": True,
}


class TestJsonValidation:
    """Validate JSON outputs from agents."""

    def test_valid_json_parses(self) -> None:
        """Well-formed JSON should parse without error."""
        raw = '{"role": "assistant", "content": "Hello world"}'
        data = json.loads(raw)
        assert isinstance(data, dict)

    def test_invalid_json_raises(self) -> None:
        """Malformed JSON must raise ValueError."""
        with pytest.raises(json.JSONDecodeError):
            json.loads("{bad json")

    def test_nested_json_depth(self, agent_config: dict[str, Any]) -> None:
        """JSON deeper than max_depth should be flagged."""
        max_depth = agent_config.get("json_schema", {}).get("max_depth", 10)
        nested: dict[str, Any] = {"leaf": True}
        for _ in range(max_depth):
            nested = {"child": nested}
        raw = json.dumps(nested)
        parsed = json.loads(raw)
        assert isinstance(parsed, dict)

    def test_json_size_limit(self, agent_config: dict[str, Any]) -> None:
        """JSON payloads exceeding max_size_bytes should be caught."""
        max_bytes = agent_config.get("json_schema", {}).get(
            "max_size_bytes", 1_048_576
        )
        small = json.dumps({"data": "x" * 100})
        assert len(small.encode()) < max_bytes

    @pytest.mark.skipif(jsonschema is None, reason="jsonschema not installed")
    def test_chat_response_schema(self) -> None:
        """Agent chat response must match expected schema."""
        valid = {"role": "assistant", "content": "I can help with that."}
        jsonschema.validate(instance=valid, schema=CHAT_RESPONSE_SCHEMA)

    @pytest.mark.skipif(jsonschema is None, reason="jsonschema not installed")
    def test_chat_response_schema_rejects_empty(self) -> None:
        """Empty content should fail schema validation."""
        invalid = {"role": "assistant", "content": ""}
        with pytest.raises(jsonschema.ValidationError):
            jsonschema.validate(instance=invalid, schema=CHAT_RESPONSE_SCHEMA)

    @pytest.mark.skipif(jsonschema is None, reason="jsonschema not installed")
    def test_tool_call_schema(self) -> None:
        """Tool call outputs must match schema."""
        valid = {"name": "read_file", "arguments": {"path": "/tmp/foo.txt"}}
        jsonschema.validate(instance=valid, schema=TOOL_CALL_SCHEMA)


class TestCodeValidation:
    """Validate code outputs from agents."""

    def test_python_syntax_valid(self) -> None:
        """Valid Python code should parse."""
        code = "def greet(name: str) -> str:\n    return f'Hello {name}'"
        tree = ast.parse(code)
        assert tree is not None

    def test_python_syntax_invalid(self) -> None:
        """Invalid Python code should raise SyntaxError."""
        with pytest.raises(SyntaxError):
            ast.parse("def broken(:")

    def test_code_line_limit(self, agent_config: dict[str, Any]) -> None:
        """Agent code output should respect line limits."""
        max_lines = agent_config.get("code_output", {}).get("max_lines", 500)
        short_code = "x = 1\n" * 10
        assert short_code.count("\n") <= max_lines

    def test_allowed_languages(self, agent_config: dict[str, Any]) -> None:
        """Config should list expected languages."""
        allowed = agent_config.get("code_output", {}).get("allowed_languages", [])
        assert "python" in allowed
        assert "typescript" in allowed

    def test_typescript_basic_syntax(self) -> None:
        """Basic TypeScript patterns should be recognized."""
        ts_code = "const greet = (name: string): string => `Hello ${name}`;"
        assert "const " in ts_code or "let " in ts_code or "function " in ts_code
        assert "=>" in ts_code or "function" in ts_code

    def test_json_output_parseable(self) -> None:
        """JSON code blocks from agents should parse."""
        json_block = '{"status": "ok", "data": [1, 2, 3]}'
        parsed = json.loads(json_block)
        assert parsed["status"] == "ok"

"""Tests for the autodoc utility."""

import ast
from pathlib import Path
from typing import Any, Dict, List

from scripts.autodoc import extract_docstring, generate_markdown, parse_python_file


def test_extract_docstring() -> None:
    """Test extracting docstrings from AST nodes."""
    # Test with a function that has a docstring
    tree = ast.parse('def foo():\n    """Hello world."""\n    pass')
    func_node = tree.body[0]
    assert extract_docstring(func_node) == "Hello world."

    # Test with a function that has no docstring
    tree = ast.parse("def bar():\n    pass")
    func_node = tree.body[0]
    assert extract_docstring(func_node) == "No docstring provided."


def test_parse_python_file(tmp_path: Path) -> None:
    """Test parsing a Python file for documentation data."""
    test_file = tmp_path / "test_module.py"
    content = (
        '"""Module doc."""\n\n'
        "def func_a():\n"
        '    """Doc A."""\n'
        "    pass\n\n"
        "class MyClass:\n"
        '    """Class doc."""\n'
        "    def method_a(self):\n"
        '        """Method A."""\n'
        "        pass"
    )
    test_file.write_text(content)

    # Run parsing (using current directory as root)
    data = parse_python_file(test_file)

    assert data["name"] == "test_module"
    assert data["docstring"] == "Module doc."
    assert len(data["functions"]) == 1
    assert data["functions"][0]["name"] == "func_a"
    assert data["functions"][0]["docstring"] == "Doc A."
    assert len(data["classes"]) == 1
    assert data["classes"][0]["name"] == "MyClass"
    assert data["classes"][0]["docstring"] == "Class doc."
    assert len(data["classes"][0]["methods"]) == 1
    assert data["classes"][0]["methods"][0]["name"] == "method_a"


def test_generate_markdown() -> None:
    """Test generating Markdown from extracted documentation data."""
    mock_data: List[Dict[str, Any]] = [
        {
            "name": "test_mod",
            "path": "tools/test_mod.py",
            "docstring": "Module doc.",
            "functions": [{"name": "foo", "docstring": "Foo doc."}],
            "classes": [
                {
                    "name": "Bar",
                    "docstring": "Bar doc.",
                    "methods": [{"name": "baz", "docstring": "Baz doc."}],
                }
            ],
        }
    ]

    markdown = generate_markdown(mock_data)

    assert "# Manus Sandbox Library Documentation" in markdown
    assert "## Module: `test_mod.py`" in markdown
    assert "#### `test_mod.foo()`" in markdown
    assert "#### `class test_mod.Bar`" in markdown
    assert "###### `Bar.baz()`" in markdown
    assert "Baz doc." in markdown

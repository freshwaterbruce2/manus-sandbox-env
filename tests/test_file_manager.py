"""Tests for the file_manager utility."""

from pathlib import Path

import pytest

from tools.file_manager import find_files_by_extension, get_file_hash


@pytest.fixture
def temp_file(tmp_path: Path) -> Path:
    """Create a temporary file for testing."""
    test_file = tmp_path / "test.txt"
    test_file.write_text("Hello, Manus!")
    return test_file


def test_get_file_hash(temp_file: Path) -> None:
    """Test calculating SHA-256 hash of a file."""
    # SHA-256 of "Hello, Manus!"
    import hashlib

    content = "Hello, Manus!"
    expected_hash = hashlib.sha256(content.encode()).hexdigest()
    assert get_file_hash(str(temp_file)) == expected_hash


def test_find_files_by_extension(tmp_path: Path) -> None:
    """Test finding files by extension in a directory."""
    # Create test files
    (tmp_path / "a.py").touch()
    (tmp_path / "b.py").touch()
    (tmp_path / "c.txt").touch()

    py_files = find_files_by_extension(str(tmp_path), ".py")
    assert len(py_files) == 2
    assert any(f.endswith("a.py") for f in py_files)
    assert any(f.endswith("b.py") for f in py_files)

    txt_files = find_files_by_extension(str(tmp_path), ".txt")
    assert len(txt_files) == 1
    assert txt_files[0].endswith("c.txt")


def test_find_files_recursive(tmp_path: Path) -> None:
    """Test recursive file finding."""
    sub_dir = tmp_path / "subdir"
    sub_dir.mkdir()
    (sub_dir / "sub.py").touch()

    py_files = find_files_by_extension(str(tmp_path), ".py")
    assert len(py_files) == 1
    assert py_files[0].endswith("sub.py")

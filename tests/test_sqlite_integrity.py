"""SQLite Integrity Check Tests.

Verifies SQLite databases aren't corrupted. Schema validation,
row count sanity checks, PRAGMA integrity_check, foreign key consistency.
Works against both live databases (D:\\databases\\, D:\\learning-system\\)
and temporary test databases.
"""

from __future__ import annotations

import os
import sqlite3
from pathlib import Path
from typing import Any

import pytest

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _get_tables(conn: sqlite3.Connection) -> list[str]:
    """Get all user table names from a SQLite database."""
    cursor = conn.execute(
        "SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%'"
    )
    return [row[0] for row in cursor.fetchall()]


def _get_row_count(conn: sqlite3.Connection, table: str) -> int:
    """Get row count for a table."""
    cursor = conn.execute(f"SELECT COUNT(*) FROM [{table}]")  # noqa: S608
    return cursor.fetchone()[0]  # type: ignore[no-any-return]


def _run_integrity_check(conn: sqlite3.Connection) -> list[str]:
    """Run PRAGMA integrity_check and return results."""
    cursor = conn.execute("PRAGMA integrity_check")
    return [row[0] for row in cursor.fetchall()]


def _run_foreign_key_check(conn: sqlite3.Connection) -> list[tuple[Any, ...]]:
    """Run PRAGMA foreign_key_check and return violations."""
    cursor = conn.execute("PRAGMA foreign_key_check")
    return cursor.fetchall()


def _find_databases(directory: str, extension: str = ".db") -> list[Path]:
    """Find all SQLite database files in a directory."""
    dir_path = Path(directory)
    if not dir_path.exists():
        return []
    return list(dir_path.rglob(f"*{extension}"))


# ---------------------------------------------------------------------------
# Unit tests against temp database (always run)
# ---------------------------------------------------------------------------

class TestSQLiteHelpers:
    """Test integrity check helpers against temporary database."""

    def test_get_tables(self, sample_sqlite_db: Path) -> None:
        """Should list all user tables."""
        conn = sqlite3.connect(str(sample_sqlite_db))
        tables = _get_tables(conn)
        conn.close()
        assert "test_table" in tables
        assert "related" in tables

    def test_get_row_count(self, sample_sqlite_db: Path) -> None:
        """Should return accurate row counts."""
        conn = sqlite3.connect(str(sample_sqlite_db))
        count = _get_row_count(conn, "test_table")
        conn.close()
        assert count == 100

    def test_integrity_check_passes(self, sample_sqlite_db: Path) -> None:
        """PRAGMA integrity_check should return 'ok' for valid DB."""
        conn = sqlite3.connect(str(sample_sqlite_db))
        results = _run_integrity_check(conn)
        conn.close()
        assert results == ["ok"], f"Integrity check failed: {results}"

    def test_foreign_key_check_passes(self, sample_sqlite_db: Path) -> None:
        """PRAGMA foreign_key_check should find no violations."""
        conn = sqlite3.connect(str(sample_sqlite_db))
        violations = _run_foreign_key_check(conn)
        conn.close()
        assert violations == [], f"FK violations: {violations}"

    def test_schema_has_expected_columns(self, sample_sqlite_db: Path) -> None:
        """Tables should have expected column structure."""
        conn = sqlite3.connect(str(sample_sqlite_db))
        cursor = conn.execute("PRAGMA table_info(test_table)")
        columns = {row[1]: row[2] for row in cursor.fetchall()}
        conn.close()

        assert "id" in columns
        assert "name" in columns
        assert "value" in columns
        assert columns["name"] == "TEXT"
        assert columns["value"] == "REAL"


class TestCorruptionDetection:
    """Verify the checker catches problems."""

    def test_detects_missing_database(self, tmp_path: Path) -> None:
        """Should handle missing database files gracefully."""
        fake_db = tmp_path / "nonexistent.db"
        assert not fake_db.exists()
        dbs = _find_databases(str(tmp_path), ".db")
        assert fake_db not in dbs

    def test_empty_database_has_no_tables(self, tmp_path: Path) -> None:
        """An empty database should have zero user tables."""
        empty_db = tmp_path / "empty.db"
        conn = sqlite3.connect(str(empty_db))
        tables = _get_tables(conn)
        conn.close()
        assert tables == []

    def test_row_count_sanity_check(self, sample_sqlite_db: Path) -> None:
        """Row counts should be within sane bounds."""
        max_rows = 10_000_000
        conn = sqlite3.connect(str(sample_sqlite_db))
        tables = _get_tables(conn)
        for table in tables:
            count = _get_row_count(conn, table)
            assert count <= max_rows, f"Table {table} has {count} rows (max: {max_rows})"
        conn.close()


# ---------------------------------------------------------------------------
# Live tests against actual databases (only on Windows with D:\ mounted)
# ---------------------------------------------------------------------------

class TestLiveDatabases:
    """Run integrity checks against real databases on D:\\ drive."""

    @pytest.fixture(autouse=True)
    def _require_windows_drives(self) -> None:
        if os.name != "nt":
            pytest.skip("Live database tests require Windows with D:\\ drive")

    def test_databases_directory_integrity(
        self, sqlite_config: dict[str, Any]
    ) -> None:
        """All .db files in configured directories pass integrity check."""
        for db_cfg in sqlite_config.get("databases", []):
            db_dir = db_cfg["path"]
            ext = db_cfg.get("extension", ".db")
            db_files = _find_databases(db_dir, ext)

            if not db_files:
                pytest.skip(f"No databases found in {db_dir}")

            for db_path in db_files:
                conn = sqlite3.connect(str(db_path))
                try:
                    results = _run_integrity_check(conn)
                    assert results == ["ok"], (
                        f"INTEGRITY FAIL: {db_path.name} — {results}"
                    )
                finally:
                    conn.close()

    def test_databases_foreign_key_consistency(
        self, sqlite_config: dict[str, Any]
    ) -> None:
        """All databases should have consistent foreign keys."""
        for db_cfg in sqlite_config.get("databases", []):
            db_dir = db_cfg["path"]
            ext = db_cfg.get("extension", ".db")
            db_files = _find_databases(db_dir, ext)

            for db_path in db_files:
                conn = sqlite3.connect(str(db_path))
                try:
                    violations = _run_foreign_key_check(conn)
                    assert violations == [], (
                        f"FK VIOLATIONS in {db_path.name}: {violations[:5]}"
                    )
                finally:
                    conn.close()

    def test_databases_row_count_sanity(
        self, sqlite_config: dict[str, Any]
    ) -> None:
        """No table should exceed configured max row count."""
        for db_cfg in sqlite_config.get("databases", []):
            db_dir = db_cfg["path"]
            ext = db_cfg.get("extension", ".db")
            max_rows = db_cfg.get("max_row_count", 10_000_000)
            db_files = _find_databases(db_dir, ext)

            for db_path in db_files:
                conn = sqlite3.connect(str(db_path))
                try:
                    tables = _get_tables(conn)
                    for table in tables:
                        count = _get_row_count(conn, table)
                        assert count <= max_rows, (
                            f"{db_path.name}.{table}: {count} rows (max: {max_rows})"
                        )
                finally:
                    conn.close()
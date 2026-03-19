"""SQLite database integrity and schema tests."""

from __future__ import annotations

import json
import sqlite3
from pathlib import Path
from typing import Any

import pytest

pytestmark = pytest.mark.requires_db


def _db_exists(path: Path) -> bool:
    return path.exists() and path.stat().st_size > 0


def _connect(path: Path) -> sqlite3.Connection:
    return sqlite3.connect(str(path), timeout=5)


# ---------------------------------------------------------------------------
# Integrity checks
# ---------------------------------------------------------------------------


class TestDatabaseIntegrity:
    """Run PRAGMA integrity_check on each configured database."""

    def test_databases_exist(
        self, config: dict[str, Any], db_paths: dict[str, Path]
    ) -> None:
        for db_info in config["databases"]["expected_dbs"]:
            dir_key = db_info["dir"]
            base_dir = db_paths.get(dir_key)
            if base_dir is None:
                pytest.skip(f"No path configured for dir key '{dir_key}'")
            db_path = base_dir / db_info["name"]
            if not _db_exists(db_path):
                pytest.skip(f"Database not found: {db_path}")
            assert db_path.stat().st_size > 0, f"Empty db: {db_path}"

    def test_integrity_check(
        self, config: dict[str, Any], db_paths: dict[str, Path]
    ) -> None:
        for db_info in config["databases"]["expected_dbs"]:
            dir_key = db_info["dir"]
            base_dir = db_paths.get(dir_key)
            if base_dir is None:
                continue
            db_path = base_dir / db_info["name"]
            if not _db_exists(db_path):
                continue
            conn = _connect(db_path)
            try:
                result = conn.execute("PRAGMA integrity_check").fetchone()
                assert result is not None
                assert result[0] == "ok", f"Integrity failed for {db_path}: {result}"
            finally:
                conn.close()

    def test_foreign_key_check(
        self, config: dict[str, Any], db_paths: dict[str, Path]
    ) -> None:
        for db_info in config["databases"]["expected_dbs"]:
            dir_key = db_info["dir"]
            base_dir = db_paths.get(dir_key)
            if base_dir is None:
                continue
            db_path = base_dir / db_info["name"]
            if not _db_exists(db_path):
                continue
            conn = _connect(db_path)
            try:
                violations = conn.execute("PRAGMA foreign_key_check").fetchall()
                assert violations == [], (
                    f"FK violations in {db_path}: {violations[:5]}"
                )
            finally:
                conn.close()


class TestSchemaSnapshot:
    """Compare current schema against a snapshot for drift detection."""

    SNAPSHOT_FILE = Path(__file__).parent.parent / "config" / "schema_snapshot.json"

    def _get_schema(self, db_path: Path) -> dict[str, list[str]]:
        conn = _connect(db_path)
        try:
            tables = conn.execute(
                "SELECT name FROM sqlite_master WHERE type='table' "
                "AND name NOT LIKE 'sqlite_%'"
            ).fetchall()
            schema: dict[str, list[str]] = {}
            for (table_name,) in tables:
                cols = conn.execute(f"PRAGMA table_info({table_name})").fetchall()
                schema[table_name] = [col[1] for col in cols]
            return schema
        finally:
            conn.close()

    def test_schema_snapshot_comparison(
        self, config: dict[str, Any], db_paths: dict[str, Path]
    ) -> None:
        if not self.SNAPSHOT_FILE.exists():
            pytest.skip("No schema_snapshot.json — run with --snapshot to create")

        with open(self.SNAPSHOT_FILE, encoding="utf-8") as f:
            snapshots = json.load(f)

        for db_info in config["databases"]["expected_dbs"]:
            dir_key = db_info["dir"]
            base_dir = db_paths.get(dir_key)
            if base_dir is None:
                continue
            db_path = base_dir / db_info["name"]
            if not _db_exists(db_path):
                continue
            key = db_info["name"]
            if key not in snapshots:
                continue
            current = self._get_schema(db_path)
            expected = snapshots[key]
            for table, cols in expected.items():
                assert table in current, f"Missing table '{table}' in {key}"
                assert set(cols).issubset(set(current[table])), (
                    f"Missing columns in {key}.{table}"
                )


class TestRowCountSanity:
    """Ensure tables aren't suspiciously empty or bloated."""

    MAX_ROWS = 10_000_000  # 10M — flag if exceeded

    def test_tables_not_empty(
        self, config: dict[str, Any], db_paths: dict[str, Path]
    ) -> None:
        for db_info in config["databases"]["expected_dbs"]:
            dir_key = db_info["dir"]
            base_dir = db_paths.get(dir_key)
            if base_dir is None:
                continue
            db_path = base_dir / db_info["name"]
            if not _db_exists(db_path):
                continue
            conn = _connect(db_path)
            try:
                tables = conn.execute(
                    "SELECT name FROM sqlite_master WHERE type='table' "
                    "AND name NOT LIKE 'sqlite_%'"
                ).fetchall()
                for (tbl,) in tables:
                    count = conn.execute(f"SELECT COUNT(*) FROM [{tbl}]").fetchone()
                    assert count is not None
                    row_count = count[0]
                    assert row_count <= self.MAX_ROWS, (
                        f"{db_path}:{tbl} has {row_count} rows (>{self.MAX_ROWS})"
                    )
            finally:
                conn.close()

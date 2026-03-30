# src\claude_orchestrator\infrastructure\memory\memory_migrator.py
from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path
import sqlite3

from claude_orchestrator.infrastructure.memory.migrations import MIGRATIONS


def ensure_memory_db_initialized(db_path: Path) -> None:
    db_path.parent.mkdir(parents=True, exist_ok=True)

    with sqlite3.connect(str(db_path)) as conn:
        conn.execute("PRAGMA foreign_keys = ON;")
        _ensure_schema_migrations_table(conn)
        _apply_pending_migrations(conn)
        conn.commit()


def _ensure_schema_migrations_table(conn: sqlite3.Connection) -> None:
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS schema_migrations (
          version INTEGER PRIMARY KEY,
          applied_at TEXT NOT NULL
        );
        """
    )


def _apply_pending_migrations(conn: sqlite3.Connection) -> None:
    current_version = get_current_version(conn)

    for version, _name, statements in MIGRATIONS:
        if version <= current_version:
            continue

        for statement in statements:
            conn.execute(statement)

        conn.execute(
            """
            INSERT OR REPLACE INTO schema_migrations(version, applied_at)
            VALUES (?, ?)
            """,
            (version, _current_timestamp_text()),
        )


def get_current_version(conn: sqlite3.Connection) -> int:
    row = conn.execute(
        "SELECT MAX(version) AS version FROM schema_migrations"
    ).fetchone()
    if row is None:
        return 0

    value = row[0]
    if value is None:
        return 0

    return int(value)


def _current_timestamp_text() -> str:
    return (
        datetime.now(timezone.utc)
        .replace(microsecond=0)
        .isoformat()
        .replace("+00:00", "Z")
    )
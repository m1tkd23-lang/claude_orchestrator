# src\claude_orchestrator\infrastructure\memory\migrations.py
from __future__ import annotations


MIGRATIONS: list[tuple[int, str, list[str]]] = [
    (
        1,
        "create memory tables",
        [
            """
            CREATE TABLE IF NOT EXISTS schema_migrations (
              version INTEGER PRIMARY KEY,
              applied_at TEXT NOT NULL
            );
            """,
            """
            CREATE TABLE IF NOT EXISTS memory_records (
              memory_id TEXT PRIMARY KEY,
              memory_kind TEXT NOT NULL,
              source_task_id TEXT NOT NULL,
              source_role TEXT NOT NULL,
              source_cycle INTEGER NOT NULL,
              source_revision INTEGER NOT NULL,
              development_mode TEXT NOT NULL,

              issue_type TEXT NOT NULL,
              importance TEXT NOT NULL,

              summary TEXT NOT NULL,
              trigger_conditions_json TEXT NOT NULL,
              recommended_action_json TEXT NOT NULL,
              avoid_action_json TEXT NOT NULL,
              related_files_json TEXT NOT NULL,
              evidence_json TEXT NOT NULL,
              source_report_path TEXT NOT NULL,

              created_at TEXT NOT NULL,
              updated_at TEXT NOT NULL
            );
            """,
            """
            CREATE INDEX IF NOT EXISTS idx_memory_role
            ON memory_records(source_role);
            """,
            """
            CREATE INDEX IF NOT EXISTS idx_memory_issue_type
            ON memory_records(issue_type);
            """,
            """
            CREATE INDEX IF NOT EXISTS idx_memory_development_mode
            ON memory_records(development_mode);
            """,
            """
            CREATE INDEX IF NOT EXISTS idx_memory_importance
            ON memory_records(importance);
            """,
            """
            CREATE INDEX IF NOT EXISTS idx_memory_task
            ON memory_records(source_task_id);
            """,
        ],
    ),
]
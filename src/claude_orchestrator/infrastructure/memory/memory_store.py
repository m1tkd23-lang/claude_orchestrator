# src\claude_orchestrator\infrastructure\memory\memory_store.py
from __future__ import annotations

from pathlib import Path
import json
import sqlite3

from claude_orchestrator.infrastructure.memory.memory_migrator import (
    ensure_memory_db_initialized,
)
from claude_orchestrator.infrastructure.memory.memory_models import MemoryRecord
from claude_orchestrator.infrastructure.memory.memory_query import MemoryQuery


class MemoryStore:
    def __init__(self, db_path: Path) -> None:
        self.db_path = db_path.resolve()
        ensure_memory_db_initialized(self.db_path)

    def insert(self, record: MemoryRecord) -> None:
        with self._connect() as conn:
            conn.execute(
                """
                INSERT INTO memory_records (
                  memory_id,
                  memory_kind,
                  source_task_id,
                  source_role,
                  source_cycle,
                  source_revision,
                  development_mode,
                  issue_type,
                  importance,
                  summary,
                  trigger_conditions_json,
                  recommended_action_json,
                  avoid_action_json,
                  related_files_json,
                  evidence_json,
                  source_report_path,
                  created_at,
                  updated_at
                )
                VALUES (
                  :memory_id,
                  :memory_kind,
                  :source_task_id,
                  :source_role,
                  :source_cycle,
                  :source_revision,
                  :development_mode,
                  :issue_type,
                  :importance,
                  :summary,
                  :trigger_conditions_json,
                  :recommended_action_json,
                  :avoid_action_json,
                  :related_files_json,
                  :evidence_json,
                  :source_report_path,
                  :created_at,
                  :updated_at
                )
                """,
                self._record_to_params(record),
            )
            conn.commit()

    def search_candidates(self, query: MemoryQuery) -> list[MemoryRecord]:
        sql = """
            SELECT
              memory_id,
              memory_kind,
              source_task_id,
              source_role,
              source_cycle,
              source_revision,
              development_mode,
              issue_type,
              importance,
              summary,
              trigger_conditions_json,
              recommended_action_json,
              avoid_action_json,
              related_files_json,
              evidence_json,
              source_report_path,
              created_at,
              updated_at
            FROM memory_records
            WHERE memory_kind = ?
              AND development_mode = ?
        """
        params: list[object] = [query.memory_kind, query.development_mode]

        if query.allowed_roles:
            placeholders = ", ".join("?" for _ in query.allowed_roles)
            sql += f" AND source_role IN ({placeholders})"
            params.extend(query.allowed_roles)

        if query.allowed_issue_types:
            placeholders = ", ".join("?" for _ in query.allowed_issue_types)
            sql += f" AND issue_type IN ({placeholders})"
            params.extend(query.allowed_issue_types)

        if query.allowed_importance:
            placeholders = ", ".join("?" for _ in query.allowed_importance)
            sql += f" AND importance IN ({placeholders})"
            params.extend(query.allowed_importance)

        sql += """
            ORDER BY created_at DESC, memory_id DESC
            LIMIT ?
        """
        params.append(query.limit)

        with self._connect() as conn:
            rows = conn.execute(sql, tuple(params)).fetchall()

        return [self._row_to_record(row) for row in rows]

    def list_recent(self, limit: int = 20) -> list[MemoryRecord]:
        with self._connect() as conn:
            rows = conn.execute(
                """
                SELECT
                  memory_id,
                  memory_kind,
                  source_task_id,
                  source_role,
                  source_cycle,
                  source_revision,
                  development_mode,
                  issue_type,
                  importance,
                  summary,
                  trigger_conditions_json,
                  recommended_action_json,
                  avoid_action_json,
                  related_files_json,
                  evidence_json,
                  source_report_path,
                  created_at,
                  updated_at
                FROM memory_records
                ORDER BY created_at DESC, memory_id DESC
                LIMIT ?
                """,
                (limit,),
            ).fetchall()

        return [self._row_to_record(row) for row in rows]

    def count(self) -> int:
        with self._connect() as conn:
            row = conn.execute(
                "SELECT COUNT(*) AS count FROM memory_records"
            ).fetchone()
        if row is None:
            return 0
        return int(row[0])

    def _connect(self) -> sqlite3.Connection:
        conn = sqlite3.connect(str(self.db_path))
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA foreign_keys = ON;")
        return conn

    @staticmethod
    def _record_to_params(record: MemoryRecord) -> dict[str, object]:
        return {
            "memory_id": record.memory_id,
            "memory_kind": record.memory_kind,
            "source_task_id": record.source_task_id,
            "source_role": record.source_role,
            "source_cycle": record.source_cycle,
            "source_revision": record.source_revision,
            "development_mode": record.development_mode,
            "issue_type": record.issue_type,
            "importance": record.importance,
            "summary": record.summary,
            "trigger_conditions_json": json.dumps(
                record.trigger_conditions,
                ensure_ascii=False,
            ),
            "recommended_action_json": json.dumps(
                record.recommended_action,
                ensure_ascii=False,
            ),
            "avoid_action_json": json.dumps(
                record.avoid_action,
                ensure_ascii=False,
            ),
            "related_files_json": json.dumps(
                record.related_files,
                ensure_ascii=False,
            ),
            "evidence_json": json.dumps(
                record.evidence,
                ensure_ascii=False,
            ),
            "source_report_path": record.source_report_path,
            "created_at": record.created_at,
            "updated_at": record.updated_at,
        }

    @staticmethod
    def _row_to_record(row: sqlite3.Row) -> MemoryRecord:
        return MemoryRecord(
            memory_id=str(row["memory_id"]),
            memory_kind=str(row["memory_kind"]),
            source_task_id=str(row["source_task_id"]),
            source_role=str(row["source_role"]),
            source_cycle=int(row["source_cycle"]),
            source_revision=int(row["source_revision"]),
            development_mode=str(row["development_mode"]),
            issue_type=str(row["issue_type"]),
            importance=str(row["importance"]),
            summary=str(row["summary"]),
            trigger_conditions=_load_json_list(row["trigger_conditions_json"]),
            recommended_action=_load_json_list(row["recommended_action_json"]),
            avoid_action=_load_json_list(row["avoid_action_json"]),
            related_files=_load_json_list(row["related_files_json"]),
            evidence=_load_json_dict(row["evidence_json"]),
            source_report_path=str(row["source_report_path"]),
            created_at=str(row["created_at"]),
            updated_at=str(row["updated_at"]),
        )


def _load_json_list(value: object) -> list[str]:
    if not isinstance(value, str) or not value.strip():
        return []

    try:
        decoded = json.loads(value)
    except json.JSONDecodeError:
        return []

    if not isinstance(decoded, list):
        return []

    result: list[str] = []
    for item in decoded:
        text = str(item).strip()
        if text:
            result.append(text)
    return result


def _load_json_dict(value: object) -> dict:
    if not isinstance(value, str) or not value.strip():
        return {}

    try:
        decoded = json.loads(value)
    except json.JSONDecodeError:
        return {}

    if not isinstance(decoded, dict):
        return {}

    return decoded
# src\claude_orchestrator\application\usecases\save_memory_from_report_usecase.py
from __future__ import annotations

from pathlib import Path

from claude_orchestrator.infrastructure.memory.memory_store import MemoryStore
from claude_orchestrator.infrastructure.project_paths import ProjectPaths
from claude_orchestrator.services.memory_extractor import extract_memory_record


class SaveMemoryFromReportUseCase:
    def execute(
        self,
        *,
        repo_path: str,
        task_id: str,
        role: str,
        cycle: int,
        revision: int,
        task_json: dict,
        state_json: dict,
        report_json: dict,
        source_report_path: str,
    ) -> dict | None:
        target_repo = Path(repo_path).resolve()
        project_paths = ProjectPaths(target_repo=target_repo)
        project_paths.ensure_initialized()

        development_mode = self._load_development_mode(project_paths)
        memory_db_path = target_repo / ".claude_orchestrator" / "runtime" / "context_memory.sqlite3"

        memory_id = self._build_memory_id(
            task_id=task_id,
            role=role,
            cycle=cycle,
            revision=revision,
        )

        record = extract_memory_record(
            memory_id=memory_id,
            task_id=task_id,
            role=role,
            cycle=cycle,
            revision=revision,
            development_mode=development_mode,
            task_json=task_json,
            state_json=state_json,
            report_json=report_json,
            source_report_path=source_report_path,
        )
        if record is None:
            return None

        store = MemoryStore(memory_db_path)
        store.insert(record)

        return {
            "memory_id": record.memory_id,
            "memory_kind": record.memory_kind,
            "source_task_id": record.source_task_id,
            "source_role": record.source_role,
            "issue_type": record.issue_type,
            "importance": record.importance,
            "db_path": str(memory_db_path),
        }

    @staticmethod
    def _load_development_mode(project_paths: ProjectPaths) -> str:
        project_config = project_paths.load_project_config()
        value = str(project_config.get("development_mode", "")).strip()
        return value or "maintenance"

    @staticmethod
    def _build_memory_id(
        *,
        task_id: str,
        role: str,
        cycle: int,
        revision: int,
    ) -> str:
        normalized_task_id = str(task_id).strip()
        normalized_role = str(role).strip()
        return f"{normalized_task_id}:{normalized_role}:c{cycle}:r{revision}"
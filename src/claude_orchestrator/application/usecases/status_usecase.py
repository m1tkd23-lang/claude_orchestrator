# src\claude_orchestrator\application\usecases\status_usecase.py
from __future__ import annotations

from pathlib import Path

from claude_orchestrator.infrastructure.project_paths import ProjectPaths
from claude_orchestrator.infrastructure.task_index import TaskIndex
from claude_orchestrator.infrastructure.task_runtime import TaskRuntime


class StatusUseCase:
    def get_task_status(self, repo_path: str, task_id: str) -> dict:
        target_repo = Path(repo_path).resolve()
        runtime = TaskRuntime(target_repo=target_repo, task_id=task_id)

        task_json = runtime.load_task_json()
        state_json = runtime.load_state_json()

        return {
            "task_id": task_json["task_id"],
            "title": task_json["title"],
            "description": task_json["description"],
            "status": state_json["status"],
            "current_stage": state_json["current_stage"],
            "next_role": state_json["next_role"],
            "cycle": state_json["cycle"],
            "last_completed_role": state_json["last_completed_role"],
            "max_cycles": state_json["max_cycles"],
            "task_dir": str(runtime.task_dir),
        }

    def list_tasks(self, repo_path: str) -> list[dict]:
        target_repo = Path(repo_path).resolve()
        project_paths = ProjectPaths(target_repo=target_repo)
        project_paths.ensure_initialized()

        index = TaskIndex(tasks_root=project_paths.tasks_dir)
        return index.list_task_statuses()
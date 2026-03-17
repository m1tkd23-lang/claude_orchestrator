# src\claude_orchestrator\application\usecases\create_task_usecase.py
from __future__ import annotations

from pathlib import Path

from claude_orchestrator.core.task_factory import (
    build_state_json,
    build_task_json,
    write_json,
)
from claude_orchestrator.core.task_id import next_task_id
from claude_orchestrator.infrastructure.project_paths import ProjectPaths


class CreateTaskUseCase:
    def execute(
        self,
        repo_path: str,
        title: str,
        description: str,
        context_files: list[str] | None = None,
        constraints: list[str] | None = None,
    ) -> Path:
        target_repo = Path(repo_path).resolve()
        paths = ProjectPaths(target_repo=target_repo)

        project_config = paths.load_project_config()

        prefix = str(project_config.get("task_id_prefix", "TASK"))
        max_cycles = int(project_config.get("max_cycles", 3))

        task_id = next_task_id(paths.tasks_dir, prefix=prefix)
        task_dir = paths.tasks_dir / task_id
        inbox_dir = task_dir / "inbox"
        outbox_dir = task_dir / "outbox"
        logs_dir = task_dir / "logs"

        inbox_dir.mkdir(parents=True, exist_ok=True)
        outbox_dir.mkdir(parents=True, exist_ok=True)
        logs_dir.mkdir(parents=True, exist_ok=True)

        task_json = build_task_json(
            task_id=task_id,
            title=title,
            description=description,
            target_repo=target_repo,
            context_files=context_files,
            constraints=constraints,
        )
        state_json = build_state_json(
            task_id=task_id,
            max_cycles=max_cycles,
        )

        write_json(task_dir / "task.json", task_json)
        write_json(task_dir / "state.json", state_json)

        return task_dir
# src\claude_orchestrator\application\usecases\init_project_usecase.py
from __future__ import annotations

from pathlib import Path

from claude_orchestrator.infrastructure.project_initializer import ProjectInitializer


class InitProjectUseCase:
    def execute(self, repo_path: str, force: bool = False) -> Path:
        target_repo = Path(repo_path).resolve()
        initializer = ProjectInitializer(target_repo=target_repo)
        return initializer.initialize(force=force)
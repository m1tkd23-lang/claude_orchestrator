# src\claude_orchestrator\application\usecases\load_requirements_usecase.py
from __future__ import annotations

from pathlib import Path
from typing import Any

from claude_orchestrator.infrastructure.requirements_runtime import RequirementsRuntime


class LoadRequirementsUseCase:
    """requirements 関連ファイルを読み込む."""

    def execute(self, repo_path: str) -> dict[str, Any]:
        repo_root = Path(repo_path).resolve()
        runtime = RequirementsRuntime(repo_root)

        try:
            requirements_json = runtime.load_requirements_json()
        except FileNotFoundError as exc:
            return {
                "ok": False,
                "repo_path": str(repo_root),
                "requirements_path": str(runtime.paths.requirements_json),
                "open_questions_path": str(runtime.paths.open_questions_json),
                "change_log_path": str(runtime.paths.requirements_change_log_json),
                "requirements": None,
                "open_questions": None,
                "change_log": None,
                "errors": [str(exc)],
            }

        open_questions_json = runtime.load_open_questions_json()
        change_log_json = runtime.load_change_log_json()

        return {
            "ok": True,
            "repo_path": str(repo_root),
            "requirements_path": str(runtime.paths.requirements_json),
            "open_questions_path": str(runtime.paths.open_questions_json),
            "change_log_path": str(runtime.paths.requirements_change_log_json),
            "requirements": requirements_json,
            "open_questions": open_questions_json,
            "change_log": change_log_json,
            "errors": [],
        }
# src\claude_orchestrator\application\usecases\validate_report_usecase.py
from __future__ import annotations

from pathlib import Path
import json

from claude_orchestrator.infrastructure.schema_validator import SchemaValidator
from claude_orchestrator.infrastructure.task_runtime import TaskRuntime


class ValidateReportUseCase:
    def execute(self, repo_path: str, task_id: str, role: str) -> dict:
        target_repo = Path(repo_path).resolve()
        runtime = TaskRuntime(target_repo=target_repo, task_id=task_id)

        task_json = runtime.load_task_json()
        state_json = runtime.load_state_json()
        cycle = int(state_json["cycle"])

        report_path = runtime.get_output_json_path(role, cycle)
        if not report_path.exists():
            raise FileNotFoundError(f"Report file not found: {report_path}")

        with report_path.open("r", encoding="utf-8") as f:
            report = json.load(f)

        validator = SchemaValidator(runtime.schemas_dir)
        validator.validate_report(role=role, data=report)

        self._check_identity(
            task_id=task_json["task_id"],
            expected_role=role,
            expected_cycle=cycle,
            report=report,
        )

        return {
            "task_id": task_id,
            "role": role,
            "cycle": cycle,
            "report_path": str(report_path),
            "valid": True,
        }

    @staticmethod
    def _check_identity(
        task_id: str,
        expected_role: str,
        expected_cycle: int,
        report: dict,
    ) -> None:
        if str(report.get("task_id")) != str(task_id):
            raise ValueError(
                f"task_id mismatch: expected={task_id}, actual={report.get('task_id')}"
            )

        if str(report.get("role")) != expected_role:
            raise ValueError(
                f"role mismatch: expected={expected_role}, actual={report.get('role')}"
            )

        if int(report.get("cycle")) != int(expected_cycle):
            raise ValueError(
                f"cycle mismatch: expected={expected_cycle}, actual={report.get('cycle')}"
            )
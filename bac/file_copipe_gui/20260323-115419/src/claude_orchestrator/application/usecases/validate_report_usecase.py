# src\claude_orchestrator\application\usecases\validate_report_usecase.py
from __future__ import annotations

from pathlib import Path
import json

from claude_orchestrator.infrastructure.schema_validator import SchemaValidator
from claude_orchestrator.infrastructure.task_runtime import TaskRuntime


class ValidateReportUseCase:
    def execute(
        self,
        repo_path: str,
        task_id: str,
        role: str,
        expected_cycle: int,
    ) -> dict:
        target_repo = Path(repo_path).resolve()
        runtime = TaskRuntime(target_repo=target_repo, task_id=task_id)

        task_json = runtime.load_task_json()
        cycle = int(expected_cycle)

        report_path = runtime.get_output_json_path(role, cycle)
        if not report_path.exists():
            raise FileNotFoundError(f"Report file not found: {report_path}")

        with report_path.open("r", encoding="utf-8") as file:
            report = json.load(file)

        validator = SchemaValidator(runtime.schemas_dir)
        validator.validate_report(role=role, data=report)

        self._check_identity(
            task_id=task_json["task_id"],
            expected_role=role,
            expected_cycle=cycle,
            report=report,
        )
        self._check_quality_gate(role=role, report=report)

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

        actual_cycle = int(report.get("cycle"))
        if actual_cycle != int(expected_cycle):
            raise ValueError(
                f"cycle mismatch: expected={expected_cycle}, actual={actual_cycle}"
            )

    @staticmethod
    def _check_quality_gate(*, role: str, report: dict) -> None:
        if role == "implementer":
            status = str(report.get("status", "")).strip()
            if status not in {"done", "blocked"}:
                raise ValueError(
                    "implementer status must be 'done' or 'blocked': "
                    f"actual={status}"
                )

        if role == "reviewer":
            decision = str(report.get("decision", "")).strip()
            if decision not in {"ok", "needs_fix"}:
                raise ValueError(
                    "reviewer decision must be 'ok' or 'needs_fix': "
                    f"actual={decision}"
                )

        if role == "director":
            final_action = str(report.get("final_action", "")).strip()
            if final_action not in {"approve", "revise", "stop"}:
                raise ValueError(
                    "director final_action must be 'approve', 'revise', or 'stop': "
                    f"actual={final_action}"
                )

        if role == "task_router":
            task_type = str(report.get("task_type", "")).strip()
            risk_level = str(report.get("risk_level", "")).strip()
            if not task_type:
                raise ValueError("task_router task_type must not be empty")
            if not risk_level:
                raise ValueError("task_router risk_level must not be empty")
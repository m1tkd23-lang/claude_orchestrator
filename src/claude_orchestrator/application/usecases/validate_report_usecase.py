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

        if int(report.get("cycle")) != int(expected_cycle):
            raise ValueError(
                f"cycle mismatch: expected={expected_cycle}, actual={report.get('cycle')}"
            )

    def _check_quality_gate(self, role: str, report: dict) -> None:
        if role == "task_router":
            self._check_task_router_quality(report)
            return

        if role == "implementer":
            self._check_implementer_quality(report)
            return

        if role == "reviewer":
            self._check_reviewer_quality(report)
            return

        if role == "director":
            self._check_director_quality(report)
            return

        raise ValueError(f"Unsupported role for quality gate: {role}")

    def _check_task_router_quality(self, report: dict) -> None:
        used_skills = self._as_string_list(report.get("used_skills"))
        reasons = self._as_string_list(report.get("skill_selection_reason"))
        notes = self._as_string_list(report.get("initial_execution_notes"))
        role_skill_plan = report.get("role_skill_plan", {}) or {}
        status = str(report.get("status", ""))

        if not used_skills:
            raise ValueError("quality gate failed for task_router: used_skills is empty")

        if "route-task" not in used_skills:
            raise ValueError(
                "quality gate failed for task_router: used_skills must include route-task"
            )

        if not reasons:
            raise ValueError(
                "quality gate failed for task_router: skill_selection_reason is empty"
            )

        if not notes:
            raise ValueError(
                "quality gate failed for task_router: initial_execution_notes is empty"
            )

        for required_role in ("implementer", "reviewer", "director"):
            if required_role not in role_skill_plan:
                raise ValueError(
                    "quality gate failed for task_router: "
                    f"role_skill_plan.{required_role} is missing"
                )

        if status == "ready":
            if not isinstance(role_skill_plan, dict):
                raise ValueError(
                    "quality gate failed for task_router: role_skill_plan must be an object"
                )

    def _check_implementer_quality(self, report: dict) -> None:
        status = str(report.get("status", ""))
        summary = self._as_text(report.get("summary"))
        changed_files = self._as_string_list(report.get("changed_files"))
        commands_run = self._as_string_list(report.get("commands_run"))
        results = report.get("results", [])
        risks = self._as_string_list(report.get("risks"))
        questions = self._as_string_list(report.get("questions"))

        if not summary:
            raise ValueError("quality gate failed for implementer: summary is empty")

        if status == "done":
            has_execution_evidence = bool(changed_files or commands_run or results)
            if not has_execution_evidence:
                raise ValueError(
                    "quality gate failed for implementer: "
                    "done report must include at least one of changed_files, commands_run, results"
                )

        if status in ("blocked", "need_input"):
            if not (risks or questions):
                raise ValueError(
                    "quality gate failed for implementer: "
                    "blocked/need_input report must include risks or questions"
                )

    def _check_reviewer_quality(self, report: dict) -> None:
        decision = str(report.get("decision", ""))
        summary = self._as_text(report.get("summary"))
        must_fix = self._as_string_list(report.get("must_fix"))
        nice_to_have = self._as_string_list(report.get("nice_to_have"))
        risks = self._as_string_list(report.get("risks"))

        if not summary:
            raise ValueError("quality gate failed for reviewer: summary is empty")

        if decision in ("ok", "needs_fix"):
            has_review_basis = bool(must_fix or nice_to_have or risks)
            if not has_review_basis:
                raise ValueError(
                    "quality gate failed for reviewer: "
                    "ok/needs_fix report must include at least one of must_fix, nice_to_have, risks"
                )

        if decision == "blocked" and not risks:
            raise ValueError(
                "quality gate failed for reviewer: blocked report must include risks"
            )

    def _check_director_quality(self, report: dict) -> None:
        final_action = str(report.get("final_action", ""))
        summary = self._as_text(report.get("summary"))
        next_actions = self._as_string_list(report.get("next_actions"))

        if not summary:
            raise ValueError("quality gate failed for director: summary is empty")

        if final_action == "revise" and not next_actions:
            raise ValueError(
                "quality gate failed for director: revise report must include next_actions"
            )

    @staticmethod
    def _as_text(value: object) -> str:
        if value is None:
            return ""
        return str(value).strip()

    @staticmethod
    def _as_string_list(value: object) -> list[str]:
        if not isinstance(value, list):
            return []
        result: list[str] = []
        for item in value:
            text = str(item).strip()
            if text:
                result.append(text)
        return result
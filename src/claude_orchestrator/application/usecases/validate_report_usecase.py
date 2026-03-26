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
        expected_revision: int,
    ) -> dict:
        target_repo = Path(repo_path).resolve()
        runtime = TaskRuntime(target_repo=target_repo, task_id=task_id)

        task_json = runtime.load_task_json()
        state_json = runtime.load_state_json()
        cycle = int(expected_cycle)
        revision = int(expected_revision)

        self._check_state_revision(
            state_json=state_json,
            expected_revision=revision,
        )

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
            "revision": revision,
            "report_path": str(report_path),
            "valid": True,
        }

    @staticmethod
    def _check_state_revision(
        *,
        state_json: dict,
        expected_revision: int,
    ) -> None:
        actual_revision = int(state_json.get("revision", 1))
        if actual_revision != int(expected_revision):
            raise ValueError(
                "state revision mismatch: "
                f"expected_revision={expected_revision}, actual_revision={actual_revision}"
            )

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

    @classmethod
    def _check_quality_gate(cls, *, role: str, report: dict) -> None:
        if role == "implementer":
            cls._check_implementer_quality_gate(report)
            return

        if role == "reviewer":
            cls._check_reviewer_quality_gate(report)
            return

        if role == "director":
            cls._check_director_quality_gate(report)
            return

        if role == "task_router":
            cls._check_task_router_quality_gate(report)
            return

    @staticmethod
    def _check_implementer_quality_gate(report: dict) -> None:
        status = str(report.get("status", "")).strip()
        if status not in {"done", "blocked", "need_input"}:
            raise ValueError(
                "implementer status must be 'done', 'blocked', or 'need_input': "
                f"actual={status}"
            )

        docs_update_result = report.get("docs_update_result")
        if not isinstance(docs_update_result, dict):
            raise ValueError("implementer docs_update_result must be an object")

        required_keys = {
            "update_performed",
            "updated_docs",
            "update_summary",
            "pending_followup_docs",
        }
        missing_keys = required_keys - set(docs_update_result.keys())
        if missing_keys:
            missing = ", ".join(sorted(missing_keys))
            raise ValueError(
                "implementer docs_update_result is missing required field(s): "
                f"{missing}"
            )

        update_performed = docs_update_result.get("update_performed")
        updated_docs = docs_update_result.get("updated_docs")
        update_summary = docs_update_result.get("update_summary")
        pending_followup_docs = docs_update_result.get("pending_followup_docs")

        if not isinstance(update_performed, bool):
            raise ValueError(
                "implementer docs_update_result.update_performed must be boolean"
            )
        if not isinstance(updated_docs, list):
            raise ValueError(
                "implementer docs_update_result.updated_docs must be an array"
            )
        if not isinstance(update_summary, str):
            raise ValueError(
                "implementer docs_update_result.update_summary must be a string"
            )
        if not isinstance(pending_followup_docs, list):
            raise ValueError(
                "implementer docs_update_result.pending_followup_docs must be an array"
            )

        if update_performed:
            if not updated_docs:
                raise ValueError(
                    "implementer docs_update_result.updated_docs must not be empty "
                    "when update_performed is true"
                )
            if not update_summary.strip():
                raise ValueError(
                    "implementer docs_update_result.update_summary must not be empty "
                    "when update_performed is true"
                )

    @staticmethod
    def _check_reviewer_quality_gate(report: dict) -> None:
        decision = str(report.get("decision", "")).strip()
        if decision not in {"ok", "needs_fix", "blocked"}:
            raise ValueError(
                "reviewer decision must be 'ok', 'needs_fix', or 'blocked': "
                f"actual={decision}"
            )

        docs_review_result = report.get("docs_review_result")
        if not isinstance(docs_review_result, dict):
            raise ValueError("reviewer docs_review_result must be an object")

        required_keys = {
            "checked",
            "consistency_ok",
            "issues",
            "notes",
        }
        missing_keys = required_keys - set(docs_review_result.keys())
        if missing_keys:
            missing = ", ".join(sorted(missing_keys))
            raise ValueError(
                "reviewer docs_review_result is missing required field(s): "
                f"{missing}"
            )

        checked = docs_review_result.get("checked")
        consistency_ok = docs_review_result.get("consistency_ok")
        issues = docs_review_result.get("issues")
        notes = docs_review_result.get("notes")

        if not isinstance(checked, bool):
            raise ValueError("reviewer docs_review_result.checked must be boolean")
        if not isinstance(consistency_ok, bool):
            raise ValueError(
                "reviewer docs_review_result.consistency_ok must be boolean"
            )
        if not isinstance(issues, list):
            raise ValueError("reviewer docs_review_result.issues must be an array")
        if not isinstance(notes, list):
            raise ValueError("reviewer docs_review_result.notes must be an array")

    @staticmethod
    def _check_director_quality_gate(report: dict) -> None:
        final_action = str(report.get("final_action", "")).strip()
        if final_action not in {"approve", "revise", "stop"}:
            raise ValueError(
                "director final_action must be 'approve', 'revise', or 'stop': "
                f"actual={final_action}"
            )

        docs_decision = report.get("docs_decision")
        if not isinstance(docs_decision, dict):
            raise ValueError("director docs_decision must be an object")

        required_keys = {
            "status",
            "reason",
            "followup_actions",
        }
        missing_keys = required_keys - set(docs_decision.keys())
        if missing_keys:
            missing = ", ".join(sorted(missing_keys))
            raise ValueError(
                "director docs_decision is missing required field(s): "
                f"{missing}"
            )

        status = str(docs_decision.get("status", "")).strip()
        reason = docs_decision.get("reason")
        followup_actions = docs_decision.get("followup_actions")

        if status not in {"sufficient", "followup_needed", "not_applicable"}:
            raise ValueError(
                "director docs_decision.status must be "
                "'sufficient', 'followup_needed', or 'not_applicable': "
                f"actual={status}"
            )

        if not isinstance(reason, str) or not reason.strip():
            raise ValueError(
                "director docs_decision.reason must be a non-empty string"
            )

        if not isinstance(followup_actions, list):
            raise ValueError(
                "director docs_decision.followup_actions must be an array"
            )

        if status == "followup_needed" and not followup_actions:
            raise ValueError(
                "director docs_decision.followup_actions must not be empty "
                "when status is 'followup_needed'"
            )

    @staticmethod
    def _check_task_router_quality_gate(report: dict) -> None:
        task_type = str(report.get("task_type", "")).strip()
        risk_level = str(report.get("risk_level", "")).strip()
        docs_update_plan = report.get("docs_update_plan")

        if not task_type:
            raise ValueError("task_router task_type must not be empty")
        if not risk_level:
            raise ValueError("task_router risk_level must not be empty")

        if not isinstance(docs_update_plan, dict):
            raise ValueError("task_router docs_update_plan must be an object")

        required_keys = {
            "needs_update",
            "target_docs",
            "update_reason",
            "update_instructions",
        }
        missing_keys = required_keys - set(docs_update_plan.keys())
        if missing_keys:
            missing = ", ".join(sorted(missing_keys))
            raise ValueError(
                "task_router docs_update_plan is missing required field(s): "
                f"{missing}"
            )

        if not isinstance(docs_update_plan.get("needs_update"), bool):
            raise ValueError(
                "task_router docs_update_plan.needs_update must be boolean"
            )

        if not isinstance(docs_update_plan.get("target_docs"), list):
            raise ValueError(
                "task_router docs_update_plan.target_docs must be an array"
            )

        if not isinstance(docs_update_plan.get("update_reason"), str):
            raise ValueError(
                "task_router docs_update_plan.update_reason must be a string"
            )

        if not isinstance(docs_update_plan.get("update_instructions"), list):
            raise ValueError(
                "task_router docs_update_plan.update_instructions must be an array"
            )

        if docs_update_plan["needs_update"]:
            if not docs_update_plan["target_docs"]:
                raise ValueError(
                    "task_router docs_update_plan.target_docs must not be empty "
                    "when needs_update is true"
                )
            if not str(docs_update_plan["update_reason"]).strip():
                raise ValueError(
                    "task_router docs_update_plan.update_reason must not be empty "
                    "when needs_update is true"
                )
            if not docs_update_plan["update_instructions"]:
                raise ValueError(
                    "task_router docs_update_plan.update_instructions must not be empty "
                    "when needs_update is true"
                )
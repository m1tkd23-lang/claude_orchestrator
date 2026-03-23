# src\claude_orchestrator\application\usecases\advance_task_usecase.py
from __future__ import annotations

from pathlib import Path
import json

from claude_orchestrator.application.usecases.validate_report_usecase import (
    ValidateReportUseCase,
)
from claude_orchestrator.core.task_factory import write_json
from claude_orchestrator.core.workflow import decide_next_from_report
from claude_orchestrator.infrastructure.task_runtime import TaskRuntime


class AdvanceTaskUseCase:
    def execute(
        self,
        repo_path: str,
        task_id: str,
        expected_role: str,
        expected_cycle: int,
        expected_revision: int,
    ) -> dict:
        target_repo = Path(repo_path).resolve()
        runtime = TaskRuntime(target_repo=target_repo, task_id=task_id)

        state_json = runtime.load_state_json()
        current_role = str(state_json["next_role"])
        current_cycle = int(state_json["cycle"])
        current_revision = int(state_json.get("revision", 1))
        max_cycles = int(state_json["max_cycles"])

        if current_role == "none":
            raise ValueError(f"Task already finished or blocked: {task_id}")

        if current_role != str(expected_role):
            raise ValueError(
                "state drift detected: "
                f"expected_role={expected_role}, actual_role={current_role}"
            )

        if current_cycle != int(expected_cycle):
            raise ValueError(
                "state drift detected: "
                f"expected_cycle={expected_cycle}, actual_cycle={current_cycle}"
            )

        if current_revision != int(expected_revision):
            raise ValueError(
                "state revision mismatch: "
                f"expected_revision={expected_revision}, actual_revision={current_revision}"
            )

        ValidateReportUseCase().execute(
            repo_path=repo_path,
            task_id=task_id,
            role=current_role,
            expected_cycle=current_cycle,
            expected_revision=current_revision,
        )

        report_path = runtime.get_output_json_path(current_role, current_cycle)
        with report_path.open("r", encoding="utf-8") as f:
            report = json.load(f)

        if current_role == "task_router":
            self._apply_task_router_result(runtime=runtime, report=report)

        next_state_values = decide_next_from_report(
            role=current_role,
            report=report,
            current_cycle=current_cycle,
            max_cycles=max_cycles,
        )

        new_state = dict(state_json)
        new_state["cycle"] = next_state_values["cycle"]
        new_state["revision"] = current_revision + 1
        new_state["status"] = next_state_values["status"]
        new_state["current_stage"] = next_state_values["current_stage"]
        new_state["next_role"] = next_state_values["next_role"]
        new_state["last_completed_role"] = next_state_values["last_completed_role"]

        write_json(runtime.state_json_path, new_state)

        return {
            "task_id": task_id,
            "status": new_state["status"],
            "current_stage": new_state["current_stage"],
            "next_role": new_state["next_role"],
            "cycle": new_state["cycle"],
            "revision": new_state["revision"],
            "state_path": str(runtime.state_json_path),
        }

    @staticmethod
    def _apply_task_router_result(runtime: TaskRuntime, report: dict) -> None:
        task_json = runtime.load_task_json()
        updated_task = dict(task_json)

        role_skill_plan = report.get("role_skill_plan", {}) or {}

        updated_task["task_type"] = report.get("task_type")
        updated_task["risk_level"] = report.get("risk_level")
        updated_task["role_skill_plan"] = {
            "task_router": ["route-task"],
            "implementer": list(role_skill_plan.get("implementer", [])),
            "reviewer": list(role_skill_plan.get("reviewer", [])),
            "director": list(role_skill_plan.get("director", [])),
        }
        updated_task["skill_selection_source"] = "task_router"
        updated_task["skill_selection_reason"] = list(
            report.get("skill_selection_reason", [])
        )
        updated_task["initial_execution_notes"] = list(
            report.get("initial_execution_notes", [])
        )

        write_json(runtime.task_json_path, updated_task)
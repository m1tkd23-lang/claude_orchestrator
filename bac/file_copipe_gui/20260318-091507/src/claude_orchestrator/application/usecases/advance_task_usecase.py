# src\claude_orchestrator\application\usecases\advance_task_usecase.py
from __future__ import annotations

from pathlib import Path
import json

from claude_orchestrator.core.task_factory import write_json
from claude_orchestrator.core.workflow import decide_next_from_report
from claude_orchestrator.infrastructure.task_runtime import TaskRuntime
from claude_orchestrator.application.usecases.validate_report_usecase import (
    ValidateReportUseCase,
)


class AdvanceTaskUseCase:
    def execute(self, repo_path: str, task_id: str) -> dict:
        target_repo = Path(repo_path).resolve()
        runtime = TaskRuntime(target_repo=target_repo, task_id=task_id)

        state_json = runtime.load_state_json()
        current_role = str(state_json["next_role"])
        current_cycle = int(state_json["cycle"])
        max_cycles = int(state_json["max_cycles"])

        if current_role == "none":
            raise ValueError(f"Task already finished or blocked: {task_id}")

        ValidateReportUseCase().execute(
            repo_path=repo_path,
            task_id=task_id,
            role=current_role,
        )

        report_path = runtime.get_output_json_path(current_role, current_cycle)
        with report_path.open("r", encoding="utf-8") as f:
            report = json.load(f)

        next_state_values = decide_next_from_report(
            role=current_role,
            report=report,
            current_cycle=current_cycle,
            max_cycles=max_cycles,
        )

        new_state = dict(state_json)
        new_state["cycle"] = next_state_values["cycle"]
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
            "state_path": str(runtime.state_json_path),
        }
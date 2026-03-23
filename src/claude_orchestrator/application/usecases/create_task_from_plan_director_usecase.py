# src\claude_orchestrator\application\usecases\create_task_from_plan_director_usecase.py
from __future__ import annotations

from pathlib import Path
import json

from claude_orchestrator.application.usecases.create_task_from_proposal_usecase import (
    CreateTaskFromProposalUseCase,
)
from claude_orchestrator.infrastructure.plan_director_runtime import PlanDirectorRuntime


class CreateTaskFromPlanDirectorUseCase:
    def execute(
        self,
        *,
        repo_path: str,
        source_task_id: str,
    ) -> dict:
        target_repo = Path(repo_path).resolve()
        runtime = PlanDirectorRuntime(
            target_repo=target_repo,
            source_task_id=source_task_id,
        )

        runtime.ensure_source_task_exists()

        state_json = runtime.load_source_state_json()
        cycle = int(state_json["cycle"])
        report_path = runtime.get_report_path(cycle)

        if not report_path.exists():
            raise FileNotFoundError(f"plan_director report not found: {report_path}")

        report = self._load_json(report_path)

        decision = str(report.get("decision", "")).strip()
        if decision != "adopt":
            return {
                "source_task_id": source_task_id,
                "decision": decision,
                "created": False,
                "created_task_id": None,
                "created_task_dir": None,
                "report_path": str(report_path),
            }

        selected_proposal_id = report.get("selected_proposal_id")
        selected_planner_role = report.get("selected_planner_role")

        if not isinstance(selected_proposal_id, str) or not selected_proposal_id.strip():
            raise ValueError(
                "selected_proposal_id is empty although decision is adopt."
            )

        if selected_planner_role not in {"planner_safe", "planner_improvement"}:
            raise ValueError(
                "selected_planner_role is invalid although decision is adopt."
            )

        created = CreateTaskFromProposalUseCase().execute(
            repo_path=repo_path,
            source_task_id=source_task_id,
            proposal_id=selected_proposal_id.strip(),
            planner_role=str(selected_planner_role),
        )

        return {
            "source_task_id": source_task_id,
            "decision": decision,
            "created": True,
            "created_task_id": created["created_task_id"],
            "created_task_dir": created["created_task_dir"],
            "selected_proposal_id": selected_proposal_id.strip(),
            "selected_planner_role": str(selected_planner_role),
            "plan_director_report_path": str(report_path),
            "proposal_state_path": created["proposal_state_path"],
        }

    @staticmethod
    def _load_json(path: Path) -> dict:
        with path.open("r", encoding="utf-8") as f:
            return json.load(f)
# src\claude_orchestrator\application\usecases\prepare_next_task_approval_usecase.py
from __future__ import annotations

from pathlib import Path

from claude_orchestrator.infrastructure.next_task_approval_store import (
    NextTaskApprovalStore,
)
from claude_orchestrator.infrastructure.plan_director_runtime import PlanDirectorRuntime


class PrepareNextTaskApprovalUseCase:
    def execute(
        self,
        *,
        repo_path: str,
        source_task_id: str,
        cycle: int,
        decision: str,
        selected_proposal_id: str,
        selected_planner_role: str,
        selection_reason: str,
        executor_type: str,
        executor_id: str,
        executor_label: str,
    ) -> dict:
        normalized_decision = str(decision).strip()
        if normalized_decision != "adopt":
            raise ValueError("approval pending can be prepared only when decision == 'adopt'")

        target_repo = Path(repo_path).resolve()
        runtime = PlanDirectorRuntime(
            target_repo=target_repo,
            source_task_id=source_task_id,
        )
        report_path = runtime.get_report_path(int(cycle))
        if not report_path.exists():
            raise FileNotFoundError(f"plan_director report not found: {report_path}")

        store = NextTaskApprovalStore(
            repo_path=str(target_repo),
            source_task_id=source_task_id,
        )
        payload = store.mark_pending(
            cycle=int(cycle),
            decision=normalized_decision,
            selected_proposal_id=str(selected_proposal_id).strip(),
            selected_planner_role=str(selected_planner_role).strip(),
            selection_reason=str(selection_reason).strip(),
            report_path=str(report_path),
            prepared_by_type=str(executor_type).strip(),
            prepared_by_id=str(executor_id).strip(),
            prepared_by_label=str(executor_label).strip(),
        )
        return {
            "prepared": True,
            "source_task_id": source_task_id,
            "approval_path": str(store.path),
            "payload": payload,
        }
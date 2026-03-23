# src\claude_orchestrator\application\usecases\approve_next_task_usecase.py
from __future__ import annotations

from pathlib import Path

from claude_orchestrator.application.usecases.create_task_from_plan_director_usecase import (
    CreateTaskFromPlanDirectorUseCase,
)
from claude_orchestrator.infrastructure.approval_lock import (
    ApprovalLock,
    ApprovalOwner,
)
from claude_orchestrator.infrastructure.next_task_approval_store import (
    NextTaskApprovalStore,
)


class ApproveNextTaskUseCase:
    def execute(
        self,
        *,
        repo_path: str,
        source_task_id: str,
        executor_type: str | None,
        executor_id: str | None,
        executor_label: str | None,
    ) -> dict:
        target_repo = str(Path(repo_path).resolve())
        owner = ApprovalOwner.normalize(
            executor_type=executor_type,
            executor_id=executor_id,
            executor_label=executor_label,
        )
        approval_lock = ApprovalLock(
            repo_path=target_repo,
            source_task_id=source_task_id,
        )
        approval_store = NextTaskApprovalStore(
            repo_path=target_repo,
            source_task_id=source_task_id,
        )
        approval_lock.acquire(owner=owner)
        try:
            payload = approval_store.load()
            if not payload:
                return {
                    "approved": False,
                    "already_processed": False,
                    "source_task_id": source_task_id,
                    "message": "承認待ちデータが見つかりません。",
                    "created_task_id": "",
                }

            status = str(payload.get("status", "")).strip()
            if status == "approved":
                return {
                    "approved": False,
                    "already_processed": True,
                    "source_task_id": source_task_id,
                    "message": "既に承認済みです。",
                    "created_task_id": str(payload.get("created_task_id", "")).strip(),
                }

            if status == "rejected":
                return {
                    "approved": False,
                    "already_processed": True,
                    "source_task_id": source_task_id,
                    "message": "既に見送り済みです。",
                    "created_task_id": "",
                }

            if status != "pending":
                raise ValueError(f"unsupported approval status: {status}")

            result = CreateTaskFromPlanDirectorUseCase().execute(
                repo_path=target_repo,
                source_task_id=source_task_id,
            )
            created_task_id = str(result.get("created_task_id") or "").strip()

            if bool(result.get("created")) and created_task_id:
                approval_store.mark_approved(
                    approver_type=owner.owner_type,
                    approver_id=owner.owner_id,
                    approver_label=owner.owner_label,
                    created_task_id=created_task_id,
                )
                return {
                    "approved": True,
                    "already_processed": False,
                    "source_task_id": source_task_id,
                    "message": "次task作成を承認しました。",
                    "created_task_id": created_task_id,
                    "selected_proposal_id": str(
                        result.get("selected_proposal_id", "")
                    ).strip(),
                    "selected_planner_role": str(
                        result.get("selected_planner_role", "")
                    ).strip(),
                }

            return {
                "approved": False,
                "already_processed": False,
                "source_task_id": source_task_id,
                "message": "plan_director の decision により task は作成されませんでした。",
                "created_task_id": "",
            }
        finally:
            approval_lock.release(owner=owner)
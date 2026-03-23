# src\claude_orchestrator\application\usecases\reject_next_task_usecase.py
from __future__ import annotations

from pathlib import Path

from claude_orchestrator.infrastructure.approval_lock import (
    ApprovalLock,
    ApprovalOwner,
)
from claude_orchestrator.infrastructure.next_task_approval_store import (
    NextTaskApprovalStore,
)


class RejectNextTaskUseCase:
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
                    "rejected": False,
                    "already_processed": False,
                    "source_task_id": source_task_id,
                    "message": "承認待ちデータが見つかりません。",
                }

            status = str(payload.get("status", "")).strip()
            if status == "approved":
                return {
                    "rejected": False,
                    "already_processed": True,
                    "source_task_id": source_task_id,
                    "message": "既に承認済みのため見送りできません。",
                }

            if status == "rejected":
                return {
                    "rejected": False,
                    "already_processed": True,
                    "source_task_id": source_task_id,
                    "message": "既に見送り済みです。",
                }

            if status != "pending":
                raise ValueError(f"unsupported approval status: {status}")

            approval_store.mark_rejected(
                rejector_type=owner.owner_type,
                rejector_id=owner.owner_id,
                rejector_label=owner.owner_label,
            )
            return {
                "rejected": True,
                "already_processed": False,
                "source_task_id": source_task_id,
                "message": "今回は次taskを作成しません。",
            }
        finally:
            approval_lock.release(owner=owner)
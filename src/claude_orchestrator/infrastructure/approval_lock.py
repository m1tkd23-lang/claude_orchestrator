# src\claude_orchestrator\infrastructure\approval_lock.py
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
import json

from claude_orchestrator.infrastructure.project_paths import ProjectPaths


class ApprovalLockedError(RuntimeError):
    def __init__(self, *, source_task_id: str, owner_label: str, started_at: str) -> None:
        suffix = f" (started_at={started_at})" if started_at else ""
        super().__init__(
            f"Next-task approval is already running by {owner_label}: "
            f"{source_task_id}{suffix}"
        )


@dataclass(frozen=True)
class ApprovalOwner:
    owner_type: str
    owner_id: str
    owner_label: str

    @classmethod
    def normalize(
        cls,
        *,
        executor_type: str | None,
        executor_id: str | None,
        executor_label: str | None,
    ) -> "ApprovalOwner":
        normalized_type = str(executor_type or "unknown").strip().lower() or "unknown"
        normalized_id = str(executor_id or normalized_type).strip() or normalized_type
        normalized_label = str(executor_label or normalized_id).strip() or normalized_id
        return cls(
            owner_type=normalized_type,
            owner_id=normalized_id,
            owner_label=normalized_label,
        )


class ApprovalLock:
    def __init__(self, *, repo_path: str, source_task_id: str) -> None:
        target_repo = Path(repo_path).resolve()
        project_paths = ProjectPaths(target_repo=target_repo)
        project_paths.ensure_initialized()
        self.repo_path = str(target_repo)
        self.source_task_id = source_task_id
        self.lock_path = (
            project_paths.tasks_dir / source_task_id / "next_task_approval_lock.json"
        )

    def acquire(self, *, owner: ApprovalOwner) -> dict:
        payload = self.load()
        if payload and self._is_conflict(payload=payload, owner=owner):
            raise ApprovalLockedError(
                source_task_id=self.source_task_id,
                owner_label=str(payload.get("owner_label", "unknown")).strip() or "unknown",
                started_at=str(payload.get("started_at", "")).strip(),
            )

        now = self._now_iso()
        lock_payload = {
            "source_task_id": self.source_task_id,
            "repo_path": self.repo_path,
            "owner_type": owner.owner_type,
            "owner_id": owner.owner_id,
            "owner_label": owner.owner_label,
            "status": "running",
            "started_at": str(payload.get("started_at", now)) if payload else now,
            "updated_at": now,
        }
        self.lock_path.parent.mkdir(parents=True, exist_ok=True)
        with self.lock_path.open("w", encoding="utf-8") as file:
            json.dump(lock_payload, file, ensure_ascii=False, indent=2)
            file.write("\n")
        return lock_payload

    def release(self, *, owner: ApprovalOwner) -> None:
        payload = self.load()
        if not payload:
            return
        if not self._is_owned_by(payload=payload, owner=owner):
            return
        self.lock_path.unlink(missing_ok=True)

    def load(self) -> dict:
        if not self.lock_path.exists():
            return {}
        with self.lock_path.open("r", encoding="utf-8") as file:
            return json.load(file)

    @staticmethod
    def _is_conflict(*, payload: dict, owner: ApprovalOwner) -> bool:
        if str(payload.get("status", "")).strip() != "running":
            return False
        return not ApprovalLock._is_owned_by(payload=payload, owner=owner)

    @staticmethod
    def _is_owned_by(*, payload: dict, owner: ApprovalOwner) -> bool:
        return (
            str(payload.get("owner_type", "")).strip() == owner.owner_type
            and str(payload.get("owner_id", "")).strip() == owner.owner_id
        )

    @staticmethod
    def _now_iso() -> str:
        return datetime.now().isoformat(timespec="seconds")
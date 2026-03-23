# src\claude_orchestrator\infrastructure\next_task_approval_store.py
from __future__ import annotations

from datetime import datetime
from pathlib import Path
import json

from claude_orchestrator.infrastructure.project_paths import ProjectPaths


class NextTaskApprovalStore:
    def __init__(self, *, repo_path: str, source_task_id: str) -> None:
        self.repo_path = str(Path(repo_path).resolve())
        self.source_task_id = str(source_task_id).strip()
        self.project_paths = ProjectPaths(target_repo=Path(self.repo_path))
        self.project_paths.ensure_initialized()
        self.path = (
            self.project_paths.tasks_dir
            / self.source_task_id
            / "next_task_approval_pending.json"
        )

    def load(self) -> dict:
        if not self.path.exists():
            return {}
        with self.path.open("r", encoding="utf-8") as file:
            return json.load(file)

    def save(self, payload: dict) -> Path:
        normalized = self._normalize_payload(payload)
        self.path.parent.mkdir(parents=True, exist_ok=True)
        with self.path.open("w", encoding="utf-8") as file:
            json.dump(normalized, file, ensure_ascii=False, indent=2)
            file.write("\n")
        return self.path

    def clear(self) -> None:
        self.path.unlink(missing_ok=True)

    def is_waiting(self) -> bool:
        payload = self.load()
        return bool(payload) and str(payload.get("status", "")).strip() == "pending"

    def mark_pending(
        self,
        *,
        cycle: int,
        decision: str,
        selected_proposal_id: str,
        selected_planner_role: str,
        selection_reason: str,
        report_path: str,
        prepared_by_type: str,
        prepared_by_id: str,
        prepared_by_label: str,
    ) -> dict:
        now = self._now_iso()
        payload = {
            "_meta": {
                "relative_path": (
                    f".claude_orchestrator/tasks/{self.source_task_id}/"
                    "next_task_approval_pending.json"
                )
            },
            "source_task_id": self.source_task_id,
            "cycle": int(cycle),
            "decision": str(decision).strip(),
            "selected_proposal_id": str(selected_proposal_id).strip(),
            "selected_planner_role": str(selected_planner_role).strip(),
            "selection_reason": str(selection_reason).strip(),
            "report_path": str(report_path).strip(),
            "status": "pending",
            "prepared_at": now,
            "prepared_by_type": str(prepared_by_type).strip(),
            "prepared_by_id": str(prepared_by_id).strip(),
            "prepared_by_label": str(prepared_by_label).strip(),
            "approved_at": "",
            "approved_by_type": "",
            "approved_by_id": "",
            "approved_by_label": "",
            "rejected_at": "",
            "rejected_by_type": "",
            "rejected_by_id": "",
            "rejected_by_label": "",
            "created_task_id": "",
            "updated_at": now,
        }
        self.save(payload)
        return payload

    def mark_approved(
        self,
        *,
        approver_type: str,
        approver_id: str,
        approver_label: str,
        created_task_id: str,
    ) -> dict:
        payload = self.load()
        if not payload:
            raise ValueError("next task approval pending data is not found.")
        now = self._now_iso()
        payload["status"] = "approved"
        payload["approved_at"] = now
        payload["approved_by_type"] = str(approver_type).strip()
        payload["approved_by_id"] = str(approver_id).strip()
        payload["approved_by_label"] = str(approver_label).strip()
        payload["created_task_id"] = str(created_task_id).strip()
        payload["updated_at"] = now
        self.save(payload)
        return payload

    def mark_rejected(
        self,
        *,
        rejector_type: str,
        rejector_id: str,
        rejector_label: str,
    ) -> dict:
        payload = self.load()
        if not payload:
            raise ValueError("next task approval pending data is not found.")
        now = self._now_iso()
        payload["status"] = "rejected"
        payload["rejected_at"] = now
        payload["rejected_by_type"] = str(rejector_type).strip()
        payload["rejected_by_id"] = str(rejector_id).strip()
        payload["rejected_by_label"] = str(rejector_label).strip()
        payload["updated_at"] = now
        self.save(payload)
        return payload

    def _normalize_payload(self, payload: dict) -> dict:
        normalized = {
            "_meta": {
                "relative_path": (
                    f".claude_orchestrator/tasks/{self.source_task_id}/"
                    "next_task_approval_pending.json"
                )
            },
            "source_task_id": self.source_task_id,
            "cycle": 0,
            "decision": "",
            "selected_proposal_id": "",
            "selected_planner_role": "",
            "selection_reason": "",
            "report_path": "",
            "status": "",
            "prepared_at": "",
            "prepared_by_type": "",
            "prepared_by_id": "",
            "prepared_by_label": "",
            "approved_at": "",
            "approved_by_type": "",
            "approved_by_id": "",
            "approved_by_label": "",
            "rejected_at": "",
            "rejected_by_type": "",
            "rejected_by_id": "",
            "rejected_by_label": "",
            "created_task_id": "",
            "updated_at": "",
            **payload,
        }
        normalized["source_task_id"] = self.source_task_id
        return normalized

    @staticmethod
    def _now_iso() -> str:
        return datetime.now().isoformat(timespec="seconds")
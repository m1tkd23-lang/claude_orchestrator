# src\claude_orchestrator\infrastructure\remote_session_store.py
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
import json

from claude_orchestrator.infrastructure.project_paths import ProjectPaths


@dataclass
class RemoteSessionInfo:
    repo_path: str
    session_name: str
    status: str
    mode: str
    last_started_at: str
    last_updated_at: str
    selected_task_id: str
    selected_source_task_id: str
    selected_proposal_id: str
    current_menu: str
    previous_menu: str
    last_message: str
    bridge_url: str
    spawn_mode: str
    permission_mode: str
    console_log_path: str
    server_pid: int | None

    approval_mode: str
    stop_after_current_task_requested: bool
    waiting_next_task_approval: bool
    last_plan_director_decision: str
    last_plan_director_selected_proposal_id: str
    last_plan_director_selection_reason: str
    last_planner_role: str
    post_run_source_task_id: str
    active_planner_role: str
    selected_proposal_planner_role: str

    def to_dict(self) -> dict:
        return {
            "repo_path": self.repo_path,
            "session_name": self.session_name,
            "status": self.status,
            "mode": self.mode,
            "last_started_at": self.last_started_at,
            "last_updated_at": self.last_updated_at,
            "selected_task_id": self.selected_task_id,
            "selected_source_task_id": self.selected_source_task_id,
            "selected_proposal_id": self.selected_proposal_id,
            "current_menu": self.current_menu,
            "previous_menu": self.previous_menu,
            "last_message": self.last_message,
            "bridge_url": self.bridge_url,
            "spawn_mode": self.spawn_mode,
            "permission_mode": self.permission_mode,
            "console_log_path": self.console_log_path,
            "server_pid": self.server_pid,
            "approval_mode": self.approval_mode,
            "stop_after_current_task_requested": self.stop_after_current_task_requested,
            "waiting_next_task_approval": self.waiting_next_task_approval,
            "last_plan_director_decision": self.last_plan_director_decision,
            "last_plan_director_selected_proposal_id": self.last_plan_director_selected_proposal_id,
            "last_plan_director_selection_reason": self.last_plan_director_selection_reason,
            "last_planner_role": self.last_planner_role,
            "post_run_source_task_id": self.post_run_source_task_id,
            "active_planner_role": self.active_planner_role,
            "selected_proposal_planner_role": self.selected_proposal_planner_role,
        }


class RemoteSessionStore:
    DEFAULT_MENU = "main"
    DEFAULT_SPAWN_MODE = "same-dir"
    DEFAULT_PERMISSION_MODE = "default"
    DEFAULT_PLANNER_ROLE = "planner_safe"

    def __init__(self, *, repo_path: str) -> None:
        self.repo_path = str(Path(repo_path).resolve())
        self.project_paths = ProjectPaths(target_repo=Path(self.repo_path))
        self.project_paths.ensure_initialized()
        self.state_path = self.project_paths.remote_session_path

    def load(self) -> dict:
        if not self.state_path.exists():
            return self._build_default_payload()

        with self.state_path.open("r", encoding="utf-8") as f:
            payload = json.load(f)

        return self._normalize_payload(payload)

    def load_info(self) -> RemoteSessionInfo:
        payload = self.load()
        return RemoteSessionInfo(
            repo_path=str(payload["repo_path"]),
            session_name=str(payload["session_name"]),
            status=str(payload["status"]),
            mode=str(payload["mode"]),
            last_started_at=str(payload["last_started_at"]),
            last_updated_at=str(payload["last_updated_at"]),
            selected_task_id=str(payload["selected_task_id"]),
            selected_source_task_id=str(payload["selected_source_task_id"]),
            selected_proposal_id=str(payload["selected_proposal_id"]),
            current_menu=str(payload["current_menu"]),
            previous_menu=str(payload["previous_menu"]),
            last_message=str(payload["last_message"]),
            bridge_url=str(payload["bridge_url"]),
            spawn_mode=str(payload["spawn_mode"]),
            permission_mode=str(payload["permission_mode"]),
            console_log_path=str(payload["console_log_path"]),
            server_pid=payload["server_pid"],
            approval_mode=str(payload["approval_mode"]),
            stop_after_current_task_requested=bool(payload["stop_after_current_task_requested"]),
            waiting_next_task_approval=bool(payload["waiting_next_task_approval"]),
            last_plan_director_decision=str(payload["last_plan_director_decision"]),
            last_plan_director_selected_proposal_id=str(
                payload["last_plan_director_selected_proposal_id"]
            ),
            last_plan_director_selection_reason=str(payload["last_plan_director_selection_reason"]),
            last_planner_role=str(payload["last_planner_role"]),
            post_run_source_task_id=str(payload["post_run_source_task_id"]),
            active_planner_role=str(payload["active_planner_role"]),
            selected_proposal_planner_role=str(payload["selected_proposal_planner_role"]),
        )

    def save(self, payload: dict) -> Path:
        normalized = self._normalize_payload(payload)
        self.state_path.parent.mkdir(parents=True, exist_ok=True)
        with self.state_path.open("w", encoding="utf-8") as f:
            json.dump(normalized, f, ensure_ascii=False, indent=2)
        return self.state_path

    def update_fields(self, **fields) -> Path:
        current = self.load()
        current.update(fields)
        current["last_updated_at"] = self._now_iso()
        return self.save(current)

    def mark_started(
        self,
        *,
        session_name: str,
        mode: str = "remote-control",
        bridge_url: str = "",
        spawn_mode: str = DEFAULT_SPAWN_MODE,
        permission_mode: str = DEFAULT_PERMISSION_MODE,
        console_log_path: str = "",
        server_pid: int | None = None,
    ) -> Path:
        now = self._now_iso()
        current = self.load()
        current["repo_path"] = self.repo_path
        current["session_name"] = str(session_name).strip()
        current["status"] = "running"
        current["mode"] = str(mode).strip() or "remote-control"
        current["last_started_at"] = now
        current["last_updated_at"] = now
        current["selected_task_id"] = ""
        current["selected_source_task_id"] = ""
        current["selected_proposal_id"] = ""
        current["current_menu"] = self.DEFAULT_MENU
        current["previous_menu"] = self.DEFAULT_MENU
        current["last_message"] = "Remote Operator を開始しました。"
        current["bridge_url"] = str(bridge_url).strip()
        current["spawn_mode"] = str(spawn_mode).strip() or self.DEFAULT_SPAWN_MODE
        current["permission_mode"] = (
            str(permission_mode).strip() or self.DEFAULT_PERMISSION_MODE
        )
        current["console_log_path"] = str(console_log_path).strip()
        current["server_pid"] = server_pid

        current["approval_mode"] = "manual"
        current["stop_after_current_task_requested"] = False
        current["waiting_next_task_approval"] = False
        current["last_plan_director_decision"] = ""
        current["last_plan_director_selected_proposal_id"] = ""
        current["last_plan_director_selection_reason"] = ""
        current["last_planner_role"] = self.DEFAULT_PLANNER_ROLE
        current["post_run_source_task_id"] = ""
        current["active_planner_role"] = self.DEFAULT_PLANNER_ROLE
        current["selected_proposal_planner_role"] = ""

        return self.save(current)

    def reset_operator_state(self) -> Path:
        current = self.load()
        current["selected_task_id"] = ""
        current["selected_source_task_id"] = ""
        current["selected_proposal_id"] = ""
        current["current_menu"] = self.DEFAULT_MENU
        current["previous_menu"] = self.DEFAULT_MENU
        current["last_message"] = ""

        current["approval_mode"] = "manual"
        current["stop_after_current_task_requested"] = False
        current["waiting_next_task_approval"] = False
        current["active_planner_role"] = self.DEFAULT_PLANNER_ROLE
        current["selected_proposal_planner_role"] = ""

        current["last_updated_at"] = self._now_iso()
        return self.save(current)

    def clear(self) -> Path:
        payload = self._build_default_payload()
        return self.save(payload)

    def _build_default_payload(self) -> dict:
        return {
            "repo_path": self.repo_path,
            "session_name": "",
            "status": "not_started",
            "mode": "remote-control",
            "last_started_at": "",
            "last_updated_at": "",
            "selected_task_id": "",
            "selected_source_task_id": "",
            "selected_proposal_id": "",
            "current_menu": self.DEFAULT_MENU,
            "previous_menu": self.DEFAULT_MENU,
            "last_message": "",
            "bridge_url": "",
            "spawn_mode": self.DEFAULT_SPAWN_MODE,
            "permission_mode": self.DEFAULT_PERMISSION_MODE,
            "console_log_path": "",
            "server_pid": None,
            "approval_mode": "manual",
            "stop_after_current_task_requested": False,
            "waiting_next_task_approval": False,
            "last_plan_director_decision": "",
            "last_plan_director_selected_proposal_id": "",
            "last_plan_director_selection_reason": "",
            "last_planner_role": self.DEFAULT_PLANNER_ROLE,
            "post_run_source_task_id": "",
            "active_planner_role": self.DEFAULT_PLANNER_ROLE,
            "selected_proposal_planner_role": "",
        }

    def _normalize_payload(self, payload: dict) -> dict:
        normalized = {
            **self._build_default_payload(),
            **payload,
        }

        for key in (
            "last_planner_role",
            "active_planner_role",
            "selected_proposal_planner_role",
        ):
            value = str(normalized.get(key, "")).strip()
            if key == "selected_proposal_planner_role" and not value:
                normalized[key] = ""
                continue
            if value not in {"planner_safe", "planner_improvement"}:
                normalized[key] = self.DEFAULT_PLANNER_ROLE
            else:
                normalized[key] = value

        approval_mode = str(normalized.get("approval_mode", "manual")).strip()
        normalized["approval_mode"] = approval_mode if approval_mode in {"manual", "auto"} else "manual"

        return normalized

    @staticmethod
    def _now_iso() -> str:
        return datetime.now().isoformat(timespec="seconds")
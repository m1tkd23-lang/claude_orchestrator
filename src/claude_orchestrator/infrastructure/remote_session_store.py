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
        }


class RemoteSessionStore:
    DEFAULT_MENU = "main"
    DEFAULT_SPAWN_MODE = "same-dir"
    DEFAULT_PERMISSION_MODE = "default"

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
        return self.save(current)

    def mark_stopped(self) -> Path:
        current = self.load()
        current["repo_path"] = self.repo_path
        current["status"] = "stopped"
        current["last_updated_at"] = self._now_iso()
        return self.save(current)

    def reset_operator_state(self) -> Path:
        current = self.load()
        current["repo_path"] = self.repo_path
        current["selected_task_id"] = ""
        current["selected_source_task_id"] = ""
        current["selected_proposal_id"] = ""
        current["current_menu"] = self.DEFAULT_MENU
        current["previous_menu"] = self.DEFAULT_MENU
        current["last_message"] = ""
        current["last_updated_at"] = self._now_iso()
        return self.save(current)

    def clear(self) -> Path:
        payload = self._build_default_payload()
        return self.save(payload)

    def exists(self) -> bool:
        return self.state_path.exists()

    def get_state_path(self) -> Path:
        return self.state_path

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
        }

    def _normalize_payload(self, payload: dict) -> dict:
        server_pid = payload.get("server_pid")
        if isinstance(server_pid, str) and server_pid.strip().isdigit():
            server_pid = int(server_pid.strip())
        elif not isinstance(server_pid, int):
            server_pid = None

        return {
            "repo_path": str(payload.get("repo_path", self.repo_path)),
            "session_name": str(payload.get("session_name", "")).strip(),
            "status": str(payload.get("status", "not_started")).strip() or "not_started",
            "mode": str(payload.get("mode", "remote-control")).strip() or "remote-control",
            "last_started_at": str(payload.get("last_started_at", "")).strip(),
            "last_updated_at": str(payload.get("last_updated_at", "")).strip()
            or self._now_iso(),
            "selected_task_id": str(payload.get("selected_task_id", "")).strip(),
            "selected_source_task_id": str(
                payload.get("selected_source_task_id", "")
            ).strip(),
            "selected_proposal_id": str(payload.get("selected_proposal_id", "")).strip(),
            "current_menu": str(payload.get("current_menu", self.DEFAULT_MENU)).strip()
            or self.DEFAULT_MENU,
            "previous_menu": str(payload.get("previous_menu", self.DEFAULT_MENU)).strip()
            or self.DEFAULT_MENU,
            "last_message": str(payload.get("last_message", "")).strip(),
            "bridge_url": str(payload.get("bridge_url", "")).strip(),
            "spawn_mode": str(
                payload.get("spawn_mode", self.DEFAULT_SPAWN_MODE)
            ).strip()
            or self.DEFAULT_SPAWN_MODE,
            "permission_mode": str(
                payload.get("permission_mode", self.DEFAULT_PERMISSION_MODE)
            ).strip()
            or self.DEFAULT_PERMISSION_MODE,
            "console_log_path": str(payload.get("console_log_path", "")).strip(),
            "server_pid": server_pid,
        }

    @staticmethod
    def _now_iso() -> str:
        return datetime.now().isoformat(timespec="seconds")
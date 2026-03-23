# src\claude_orchestrator\gui\main_window_remote.py
from __future__ import annotations

from pathlib import Path

from PySide6.QtWidgets import QApplication

from claude_orchestrator.gui.claude_runner import (
    start_claude_remote_control_session,
)
from claude_orchestrator.gui.dialog_helpers import append_log, show_error, show_info
from claude_orchestrator.gui.state_helpers import handle_repo_changed, require_repo_path
from claude_orchestrator.infrastructure.remote_session_store import RemoteSessionStore
from claude_orchestrator.gui.services.remote_prompt_service import load_remote_prompt


class MainWindowRemoteMixin:
    def on_connect_remote_claude(self) -> None:
        try:
            repo_path = require_repo_path(self)
            handle_repo_changed(self, repo_path)

            repo_name = Path(repo_path).resolve().name
            session_name = self.remote_session_name_edit.text().strip()
            if not session_name:
                session_name = f"orchestrator-remote-{repo_name}"

            spawn_mode = self.remote_spawn_mode_combo.currentText().strip() or "same-dir"
            permission_mode = (
                self.remote_permission_mode_combo.currentText().strip() or "default"
            )

            result = start_claude_remote_control_session(
                repo_path=repo_path,
                session_name=session_name,
                spawn_mode=spawn_mode,
                permission_mode=permission_mode,
            )

            store = RemoteSessionStore(repo_path=repo_path)
            state_path = store.mark_started(
                session_name=result.session_name,
                mode="remote-control",
                bridge_url=result.bridge_url,
                spawn_mode=result.spawn_mode,
                permission_mode=result.permission_mode,
                console_log_path=result.log_path,
                server_pid=result.pid,
            )

            self._load_remote_session_info_safe()

            append_log(
                self,
                "[INFO] remote Claude started: "
                f"session_name={result.session_name}, pid={result.pid}, "
                f"spawn={result.spawn_mode}, permission={result.permission_mode}",
            )

            show_info(self, "Remote Claude 接続開始", f"URL:\n{result.bridge_url}")

        except Exception as exc:
            show_error(self, "Remote Claude 接続エラー", exc)

    def on_copy_remote_operator_prompt(self) -> None:
        try:
            repo_path = require_repo_path(self)
            handle_repo_changed(self, repo_path)

            prompt = load_remote_prompt(repo_path)

            QApplication.clipboard().setText(prompt)

            append_log(self, "[INFO] remote operator prompt copied.")

            show_info(
                self,
                "コピー完了",
                "Remote Operator プロンプトをクリップボードにコピーしました。",
            )

        except Exception as exc:
            show_error(self, "プロンプトコピーエラー", exc)

    def on_reload_remote_state(self) -> None:
        try:
            repo_path = require_repo_path(self)
            handle_repo_changed(self, repo_path)
            self._load_remote_session_info_safe()
            append_log(self, "[INFO] remote session state reloaded.")
        except Exception as exc:
            show_error(self, "Remote 状態再読込エラー", exc)

    def on_copy_remote_url(self) -> None:
        bridge_url = self.remote_bridge_url_edit.text().strip()
        if not bridge_url:
            append_log(self, "[INFO] bridge_url is empty. copy skipped.")
            return

        QApplication.clipboard().setText(bridge_url)
        append_log(self, "[INFO] bridge_url copied.")

    def _reset_remote_view(self) -> None:
        self.remote_session_name_edit.clear()
        self.remote_spawn_mode_combo.setCurrentText("same-dir")
        self.remote_permission_mode_combo.setCurrentText("default")
        self.remote_status_edit.setText("not_started")
        self.remote_mode_edit.setText("remote-control")
        self.remote_last_started_at_edit.clear()
        self.remote_bridge_url_edit.clear()
        self.remote_console_log_path_edit.clear()
        self.remote_server_pid_edit.clear()
        self.remote_current_menu_edit.setText("main")
        self.remote_previous_menu_edit.setText("main")
        self.remote_selected_task_id_edit.clear()
        self.remote_selected_source_task_id_edit.clear()
        self.remote_selected_proposal_id_edit.clear()
        self.remote_last_message_edit.clear()

    def _load_remote_session_info_safe(self) -> None:
        repo_path = self.repo_path_edit.text().strip()
        if not repo_path:
            self._reset_remote_view()
            return

        try:
            store = RemoteSessionStore(repo_path=repo_path)
            info = store.load_info()

            self.remote_bridge_url_edit.setText(info.bridge_url)
            self.remote_status_edit.setText(info.status)

        except Exception:
            self._reset_remote_view()
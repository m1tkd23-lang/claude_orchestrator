# src\claude_orchestrator\gui\main_window_remote.py
from __future__ import annotations

from claude_orchestrator.gui.dialog_helpers import append_log
from claude_orchestrator.gui.state_helpers import (
    get_display_target_task_id,
    get_repo_path,
    handle_repo_changed,
    load_selected_task_detail,
    normalize_repo_path,
    refresh_task_list,
    set_active_pipeline_task,
    set_selected_task,
)
from claude_orchestrator.infrastructure.remote_session_store import RemoteSessionStore


class MainWindowRemoteMixin:
    def _start_remote_sync_timer(self) -> None:
        if self._remote_sync_timer is not None:
            return

        from PySide6.QtCore import QTimer

        self._remote_sync_timer = QTimer(self)
        self._remote_sync_timer.timeout.connect(self._sync_gui_from_repo_state)
        self._remote_sync_timer.start(self._remote_sync_interval_ms)

    def _stop_remote_sync_timer(self) -> None:
        if self._remote_sync_timer is None:
            return
        self._remote_sync_timer.stop()
        self._remote_sync_timer.deleteLater()
        self._remote_sync_timer = None

    def _resolve_remote_target_task_id(self, payload: dict) -> str:
        remote_selected_task_id = str(payload.get("selected_task_id", "")).strip()
        remote_source_task_id = str(payload.get("selected_source_task_id", "")).strip()
        remote_post_run_source_task_id = str(payload.get("post_run_source_task_id", "")).strip()

        active_task_id = str(getattr(self, "_active_pipeline_task_id", "")).strip()
        if active_task_id:
            return active_task_id

        if remote_selected_task_id:
            return remote_selected_task_id
        if remote_source_task_id:
            return remote_source_task_id
        if remote_post_run_source_task_id:
            return remote_post_run_source_task_id

        return str(getattr(self, "_selected_task_id", "")).strip()

    def _sync_gui_from_repo_state(self) -> None:
        if self._remote_sync_in_progress:
            return

        repo_path = normalize_repo_path(get_repo_path(self))
        if not repo_path:
            return

        self._remote_sync_in_progress = True
        try:
            handle_repo_changed(self, repo_path)

            store = RemoteSessionStore(repo_path=repo_path)
            payload = store.load()
            target_task_id = self._resolve_remote_target_task_id(payload)

            refresh_task_list(self)

            if target_task_id:
                if bool(getattr(self, "_follow_active_pipeline_task", True)):
                    set_active_pipeline_task(self, target_task_id)
                else:
                    set_selected_task(self, target_task_id)

                load_selected_task_detail(self, target_task_id)
                self._load_task_inbox_logs(target_task_id)
                self._load_existing_planner_data(target_task_id)

            self._refresh_remote_view_from_payload(payload)
            self._refresh_pipeline_controls()
            self._refresh_pipeline_tab()
        except Exception as exc:
            append_log(self, f"[WARN] remote sync skipped: {type(exc).__name__}: {exc}")
        finally:
            self._remote_sync_in_progress = False

    def _refresh_remote_view_from_payload(self, payload: dict) -> None:
        session_name = str(payload.get("session_name", "")).strip()
        current_menu = str(payload.get("current_menu", "")).strip()
        last_message = str(payload.get("last_message", "")).strip()

        if hasattr(self, "remote_session_name_edit"):
            self.remote_session_name_edit.setText(session_name)
        if hasattr(self, "remote_current_menu_edit"):
            self.remote_current_menu_edit.setText(current_menu)
        if hasattr(self, "remote_last_message_edit"):
            self.remote_last_message_edit.setPlainText(last_message)

    def _reset_remote_view(self) -> None:
        if hasattr(self, "remote_session_name_edit"):
            self.remote_session_name_edit.clear()
        if hasattr(self, "remote_current_menu_edit"):
            self.remote_current_menu_edit.clear()
        if hasattr(self, "remote_last_message_edit"):
            self.remote_last_message_edit.clear()
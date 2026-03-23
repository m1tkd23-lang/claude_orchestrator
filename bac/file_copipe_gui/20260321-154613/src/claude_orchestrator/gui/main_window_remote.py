# src\claude_orchestrator\gui\main_window_remote.py
from __future__ import annotations

from pathlib import Path

from PySide6.QtCore import QTimer
from PySide6.QtWidgets import QApplication

from claude_orchestrator.gui.claude_runner import (
    start_claude_remote_control_session,
)
from claude_orchestrator.gui.dialog_helpers import append_log, show_error, show_info
from claude_orchestrator.gui.state_helpers import (
    handle_repo_changed,
    load_selected_task_detail,
    refresh_task_list,
    require_repo_path,
)
from claude_orchestrator.infrastructure.remote_session_store import RemoteSessionStore
from claude_orchestrator.gui.services.remote_prompt_service import load_remote_prompt


class MainWindowRemoteMixin:
    def on_connect_remote_claude(self) -> None:
        try:
            repo_path = require_repo_path(self)
            handle_repo_changed(self, repo_path)

            session_name = self.remote_session_name_edit.text().strip()
            if not session_name:
                session_name = self._generate_default_session_name(repo_path)

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
            store.mark_started(
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
            self._sync_gui_from_repo_state(auto=False)
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

            current_session_name = self.remote_session_name_edit.text().strip()
            if current_session_name:
                session_name_to_show = current_session_name
            elif info.session_name.strip():
                session_name_to_show = info.session_name.strip()
            else:
                session_name_to_show = self._generate_default_session_name(repo_path)

            self.remote_session_name_edit.setText(session_name_to_show)
            self.remote_status_edit.setText(info.status)
            self.remote_mode_edit.setText(info.mode)
            self.remote_last_started_at_edit.setText(info.last_started_at)
            self.remote_bridge_url_edit.setText(info.bridge_url)
            self.remote_console_log_path_edit.setText(info.console_log_path)
            self.remote_server_pid_edit.setText(
                "" if info.server_pid is None else str(info.server_pid)
            )
            self.remote_current_menu_edit.setText(info.current_menu)
            self.remote_previous_menu_edit.setText(info.previous_menu)
            self.remote_selected_task_id_edit.setText(info.selected_task_id)
            self.remote_selected_source_task_id_edit.setText(info.selected_source_task_id)
            self.remote_selected_proposal_id_edit.setText(info.selected_proposal_id)
            self.remote_last_message_edit.setPlainText(info.last_message)

        except Exception:
            self._reset_remote_view()

    def _start_remote_sync_timer(self) -> None:
        if self._remote_sync_timer is not None:
            return

        self._remote_sync_timer = QTimer(self)
        self._remote_sync_timer.setInterval(self._remote_sync_interval_ms)
        self._remote_sync_timer.timeout.connect(self._on_remote_sync_timer_timeout)
        self._remote_sync_timer.start()

    def _stop_remote_sync_timer(self) -> None:
        if self._remote_sync_timer is None:
            return

        self._remote_sync_timer.stop()
        self._remote_sync_timer.deleteLater()
        self._remote_sync_timer = None

    def _on_remote_sync_timer_timeout(self) -> None:
        self._sync_gui_from_repo_state(auto=True)

    def _sync_gui_from_repo_state(self, *, auto: bool) -> None:
        repo_path = self.repo_path_edit.text().strip()
        if not repo_path:
            return

        if self._remote_sync_in_progress:
            return

        self._remote_sync_in_progress = True
        try:
            self._load_remote_session_info_safe()

            if self._auto_run_active or self._planner_active or self._plan_director_active:
                self._refresh_pipeline_tab()
                return

            store = RemoteSessionStore(repo_path=repo_path)
            info = store.load_info()

            target_task_id = self._resolve_remote_target_task_id(info)
            source_task_id = self._resolve_remote_source_task_id(info, target_task_id)

            refresh_task_list(self, log_enabled=not auto)

            if target_task_id:
                self._current_task_id = target_task_id
                load_selected_task_detail(
                    self,
                    target_task_id,
                    log_enabled=not auto,
                )
                self._load_task_inbox_logs(target_task_id)
            elif self._current_task_id:
                load_selected_task_detail(
                    self,
                    self._current_task_id,
                    log_enabled=not auto,
                )
                self._load_task_inbox_logs(self._current_task_id)

            planner_task_id = source_task_id or target_task_id or self._current_task_id
            if planner_task_id:
                self._sync_planner_views_from_task(
                    planner_task_id,
                    log_enabled=not auto,
                )

            self._refresh_pipeline_tab()

        except Exception as exc:
            if not auto:
                raise exc
        finally:
            self._remote_sync_in_progress = False

    def _sync_planner_views_from_task(self, task_id: str, *, log_enabled: bool) -> None:
        previous_current_task_id = self._current_task_id
        previous_planner_role = self._get_current_planner_role()

        try:
            self._load_existing_planner_data(task_id)

            if log_enabled:
                append_log(
                    self,
                    "[INFO] remote sync planner data loaded: "
                    f"task_id={task_id}, planner_role={self._get_current_planner_role()}",
                )
                return

            planner_report_loaded = isinstance(getattr(self, "_planner_report", None), dict)
            plan_director_report_loaded = isinstance(
                getattr(self, "_plan_director_report", None),
                dict,
            )
            if planner_report_loaded or plan_director_report_loaded:
                append_log(
                    self,
                    "[INFO] remote sync updated planner/plan_director view: "
                    f"task_id={task_id}, planner_role={self._get_current_planner_role()}",
                )

        finally:
            self._current_task_id = previous_current_task_id
            self._planner_role = previous_planner_role

            combo = getattr(self, "planner_role_combo", None)
            if combo is not None:
                target_value = previous_planner_role
                restored = False
                for index in range(combo.count()):
                    item_data = combo.itemData(index)
                    item_text = str(combo.itemText(index)).strip()
                    if item_data == target_value or item_text == target_value:
                        combo.blockSignals(True)
                        combo.setCurrentIndex(index)
                        combo.blockSignals(False)
                        restored = True
                        break
                if not restored:
                    combo.blockSignals(True)
                    combo.setCurrentText(target_value)
                    combo.blockSignals(False)

    @staticmethod
    def _resolve_remote_target_task_id(info: object) -> str:
        selected_task_id = str(getattr(info, "selected_task_id", "")).strip()
        if selected_task_id:
            return selected_task_id
        return ""

    @staticmethod
    def _resolve_remote_source_task_id(info: object, fallback_task_id: str) -> str:
        selected_source_task_id = str(
            getattr(info, "selected_source_task_id", "")
        ).strip()
        if selected_source_task_id:
            return selected_source_task_id

        post_run_source_task_id = str(
            getattr(info, "post_run_source_task_id", "")
        ).strip()
        if post_run_source_task_id:
            return post_run_source_task_id

        return fallback_task_id

    def _generate_default_session_name(self, repo_path: str) -> str:
        repo_name = Path(repo_path).resolve().name
        base_name = f"orchestrator-remote-{repo_name}"

        store = RemoteSessionStore(repo_path=repo_path)
        info = store.load_info()

        existing = str(info.session_name).strip()

        if not existing or existing != base_name:
            return base_name

        index = 1
        while True:
            candidate = f"{base_name}_{index:02d}"
            if candidate != existing:
                return candidate
            index += 1
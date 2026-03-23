# src\claude_orchestrator\gui\main_window_auto_run.py
from __future__ import annotations

from PySide6.QtCore import QThread

from claude_orchestrator.gui.auto_run_worker import AutoRunWorker
from claude_orchestrator.gui.dialog_helpers import append_log, show_error
from claude_orchestrator.gui.state_helpers import (
    handle_repo_changed,
    load_selected_task_detail,
    refresh_task_list,
    require_repo_path,
    require_selected_task_id,
    set_active_pipeline_task,
)


class MainWindowAutoRunMixin:
    def on_run_claude_step(self) -> None:
        try:
            if self._is_pipeline_busy():
                append_log(self, "[INFO] pipeline is already active.")
                return

            repo_path = require_repo_path(self)
            handle_repo_changed(self, repo_path)
            task_id = require_selected_task_id(self)

            set_active_pipeline_task(self, task_id)
            load_selected_task_detail(self, task_id)
            refresh_task_list(self)

            self._reset_execution_view()
            self._set_execution_state("starting")
            self._set_execution_step("preparing")
            self._set_execution_role(self.current_task_next_role_edit.text().strip())
            self._set_execution_cycle(self.current_task_cycle_edit.text().strip())
            self._last_auto_run_completion_status = ""
            self._pending_auto_planner_after_completion = False
            self._waiting_next_task_approval = False
            self._stop_after_current_task_requested = False
            self._pending_auto_approve_next_task = False

            if self._auto_approve_next_task:
                self._append_monitor_message(
                    "自動承認モード有効: plan_director が adopt の場合、"
                    "承認待ちをスキップして次task作成へ進みます"
                )
                append_log(
                    self,
                    "[INFO] auto approval mode is enabled for this session",
                )

            self._auto_run_active = True
            self._refresh_pipeline_controls()
            self._refresh_pipeline_tab()

            self._auto_run_thread = QThread(self)
            self._auto_run_worker = AutoRunWorker(repo_path=repo_path, task_id=task_id)
            self._auto_run_worker.moveToThread(self._auto_run_thread)

            self._auto_run_thread.started.connect(self._auto_run_worker.run)
            self._auto_run_worker.status_changed.connect(self._on_worker_status_changed)
            self._auto_run_worker.monitor_message.connect(self._on_worker_monitor_message)
            self._auto_run_worker.log_message.connect(self._on_worker_log_message)
            self._auto_run_worker.show_next_ready.connect(self._on_worker_show_next_ready)
            self._auto_run_worker.validation_ready.connect(self._on_worker_validation_ready)
            self._auto_run_worker.task_detail_requested.connect(
                self._on_worker_task_detail_requested
            )
            self._auto_run_worker.task_list_refresh_requested.connect(
                self._on_worker_task_list_refresh_requested
            )
            self._auto_run_worker.error_signal.connect(self._on_worker_error)
            self._auto_run_worker.completed_signal.connect(self._on_worker_completed)
            self._auto_run_worker.finished.connect(self._auto_run_thread.quit)
            self._auto_run_worker.finished.connect(self._auto_run_worker.deleteLater)
            self._auto_run_thread.finished.connect(self._on_auto_run_thread_finished)
            self._auto_run_thread.finished.connect(self._auto_run_thread.deleteLater)

            self._auto_run_thread.start()
        except Exception as exc:
            self._auto_run_active = False
            self._refresh_pipeline_controls()
            self._refresh_pipeline_tab()
            show_error(self, "Claude自動実行エラー", exc)

    def on_request_stop_after_current_task(self) -> None:
        try:
            if not self._auto_run_active:
                append_log(self, "[INFO] 実行中タスクが無いため停止予約は行いません。")
                return

            self._stop_after_current_task_requested = True
            self._append_monitor_message("現在のタスク完了時点で停止する予約を受け付けました")
            append_log(self, "[INFO] stop requested after current task completion")
            self._refresh_pipeline_controls()
            self._refresh_pipeline_tab()
        except Exception as exc:
            show_error(self, "停止予約エラー", exc)

    def _on_worker_status_changed(
        self,
        status: str,
        step: str,
        role: str,
        cycle: str,
    ) -> None:
        self._set_execution_state(status)
        self._set_execution_step(step)
        self._set_execution_role(role)
        self._set_execution_cycle(cycle)
        self._refresh_pipeline_tab()

    def _on_worker_monitor_message(self, message: str) -> None:
        self._append_monitor_message(message)

    def _on_worker_log_message(self, message: str) -> None:
        append_log(self, message)

    def _on_worker_show_next_ready(self, result: object) -> None:
        if isinstance(result, dict):
            self._apply_show_next_result(result)
            self._refresh_pipeline_tab()

    def _on_worker_validation_ready(self, text: str) -> None:
        self.validation_result_edit.setPlainText(text)

    def _on_worker_task_detail_requested(self, task_id: str) -> None:
        try:
            set_active_pipeline_task(self, task_id)
            load_selected_task_detail(self, task_id)
            self._refresh_pipeline_tab()
        except Exception as exc:
            show_error(self, "task詳細更新エラー", exc)

    def _on_worker_task_list_refresh_requested(self) -> None:
        try:
            refresh_task_list(self)
            self._refresh_pipeline_tab()
        except Exception as exc:
            show_error(self, "task一覧更新エラー", exc)

    def _on_worker_error(self, title: str, message: str) -> None:
        self._set_execution_state("failed")
        self._set_execution_step("stopped")
        self._append_monitor_message(message)
        append_log(self, f"[ERROR] {message}")
        self._auto_run_active = False
        self._pending_auto_planner_after_completion = False
        self._pending_auto_approve_next_task = False
        self._refresh_pipeline_controls()
        self._refresh_pipeline_tab()
        show_error(self, title, RuntimeError(message))

    def _on_worker_completed(self, task_id: str, cycle: str, status: str) -> None:
        self._last_auto_run_completion_status = status

        # director 完了後に planner 待機へ入る瞬間も同一 task を保持する
        set_active_pipeline_task(self, task_id)
        load_selected_task_detail(self, task_id)

        self._set_execution_state("completed")
        self._set_execution_step("stopped")
        self._set_execution_role("none")
        self._set_execution_cycle(cycle)
        self._append_monitor_message(f"task completed: {task_id}")
        append_log(
            self,
            f"[INFO] task completed: {task_id}, cycle={cycle}, status={status}",
        )

        if status == "completed":
            if self._stop_after_current_task_requested:
                self._pending_auto_planner_after_completion = False
                self._append_monitor_message(
                    "停止予約により、現在タスク完了後の後工程は起動しません"
                )
                append_log(
                    self,
                    "[INFO] post-task pipeline skipped because stop-after-current-task was requested",
                )
                self._set_execution_state("stopped")
                self._set_execution_step("stopped after current task")
                self._set_execution_role("none")
                self._set_execution_cycle(cycle)
                self._stop_after_current_task_requested = False
            else:
                # planner 待機中も TASK を維持する
                set_active_pipeline_task(self, task_id)
                load_selected_task_detail(self, task_id)

                self._pending_auto_planner_after_completion = True
                self._set_execution_state("running")
                self._set_execution_step("post-director planning queued")
                self._set_execution_role(self._get_current_planner_role())
                self._set_execution_cycle(cycle)
                self._append_monitor_message(
                    "director approve 後の後工程を待機中: planner を自動起動します"
                )

        self._refresh_pipeline_tab()

    def _on_auto_run_thread_finished(self) -> None:
        current_active_task_id = str(getattr(self, "_active_pipeline_task_id", "")).strip()

        self._auto_run_active = False
        self._auto_run_worker = None
        self._auto_run_thread = None

        if self._pending_auto_planner_after_completion:
            self._pending_auto_planner_after_completion = False
            try:
                if current_active_task_id:
                    set_active_pipeline_task(self, current_active_task_id)
                    load_selected_task_detail(self, current_active_task_id)

                append_log(
                    self,
                    "[INFO] director approve 後の自動後工程を開始します: "
                    f"planner_role={self._get_current_planner_role()}",
                )
                self._start_planner_generation(auto_run_plan_director=True)
            except Exception as exc:
                self._refresh_pipeline_controls()
                self._refresh_pipeline_tab()
                show_error(self, "自動後工程起動エラー", exc)
                return
        else:
            self._refresh_pipeline_controls()
            self._refresh_pipeline_tab()
# src\claude_orchestrator\gui\main_window.py
from __future__ import annotations

from pathlib import Path

from PySide6.QtCore import QThread
from PySide6.QtWidgets import QMainWindow

from claude_orchestrator.application.usecases.advance_task_usecase import (
    AdvanceTaskUseCase,
)
from claude_orchestrator.application.usecases.create_task_usecase import (
    CreateTaskUseCase,
)
from claude_orchestrator.application.usecases.init_project_usecase import (
    InitProjectUseCase,
)
from claude_orchestrator.application.usecases.show_next_usecase import (
    ShowNextUseCase,
)
from claude_orchestrator.application.usecases.validate_report_usecase import (
    ValidateReportUseCase,
)
from claude_orchestrator.gui.auto_run_worker import AutoRunWorker
from claude_orchestrator.gui.dialog_helpers import append_log, show_error, show_info
from claude_orchestrator.gui.state_helpers import (
    apply_initial_state,
    handle_repo_changed,
    load_selected_task_detail,
    parse_multiline_list,
    read_text_file_if_exists,
    refresh_task_list,
    require_repo_path,
    require_selected_task_id,
)
from claude_orchestrator.gui.ui_sections import (
    build_main_window_ui,
    connect_main_window_signals,
)
from claude_orchestrator.infrastructure.project_paths import ProjectPaths


class MainWindow(QMainWindow):
    def __init__(self) -> None:
        super().__init__()

        self.setWindowTitle("Claude Orchestrator GUI MVP")
        self.resize(1600, 950)

        self._last_prompt_path: str = ""
        self._last_output_json_path: str = ""
        self._current_task_id: str = ""
        self._last_repo_path: str = ""
        self._auto_run_thread: QThread | None = None
        self._auto_run_worker: AutoRunWorker | None = None
        self._auto_run_active: bool = False

        build_main_window_ui(self)
        connect_main_window_signals(self)
        apply_initial_state(self)
        self._reset_execution_view()

    def on_browse_repo(self) -> None:
        from PySide6.QtWidgets import QFileDialog

        selected = QFileDialog.getExistingDirectory(self, "対象 repo を選択")
        if not selected:
            return
        self.repo_path_edit.setText(selected)
        handle_repo_changed(self, selected)
        if not self._auto_run_active:
            self._reset_execution_view()

    def on_repo_path_edited(self) -> None:
        handle_repo_changed(self, self.repo_path_edit.text().strip())
        if not self._auto_run_active:
            self._reset_execution_view()

    def on_check_initialized(self) -> None:
        try:
            repo_path = require_repo_path(self)
            handle_repo_changed(self, repo_path)

            project_paths = ProjectPaths(target_repo=Path(repo_path))
            project_paths.ensure_initialized()

            append_log(self, f"[INFO] initialized repo confirmed: {project_paths.root}")
            refresh_task_list(self)
        except Exception as exc:
            show_error(self, "初期化確認エラー", exc)

    def on_init_project(self) -> None:
        try:
            repo_path = require_repo_path(self)
            handle_repo_changed(self, repo_path)

            result = InitProjectUseCase().execute(repo_path=repo_path, force=False)
            append_log(self, f"[INFO] init-project completed: {result}")
            show_info(self, "初期化完了", f"Initialized:\n{result}")
            refresh_task_list(self)
        except Exception as exc:
            show_error(self, "init-project エラー", exc)

    def on_create_task(self) -> None:
        try:
            repo_path = require_repo_path(self)
            handle_repo_changed(self, repo_path)

            title = self.task_title_edit.text().strip()
            description = self.task_desc_edit.toPlainText().strip()

            if not title:
                raise ValueError("title is required.")
            if not description:
                raise ValueError("description is required.")

            context_files = parse_multiline_list(self.context_files_edit.toPlainText())
            constraints = parse_multiline_list(self.constraints_edit.toPlainText())

            task_dir = CreateTaskUseCase().execute(
                repo_path=repo_path,
                title=title,
                description=description,
                context_files=context_files,
                constraints=constraints,
            )

            created_task_id = Path(task_dir).name

            append_log(self, f"[INFO] task created: {task_dir}")

            self.task_title_edit.clear()
            self.task_desc_edit.clear()
            self.context_files_edit.clear()
            self.constraints_edit.clear()

            self._current_task_id = created_task_id
            refresh_task_list(self)
            load_selected_task_detail(self, created_task_id)

            if not self._auto_run_active:
                self._reset_execution_view()

        except Exception as exc:
            show_error(self, "task作成エラー", exc)

    def on_refresh_tasks(self) -> None:
        try:
            repo_path = require_repo_path(self)
            handle_repo_changed(self, repo_path)
            refresh_task_list(self)
        except Exception as exc:
            show_error(self, "task一覧更新エラー", exc)

    def on_task_selected(self) -> None:
        items = self.task_list_widget.selectedItems()
        if not items:
            return

        try:
            task_id = str(items[0].data(0x0100))
            load_selected_task_detail(self, task_id)

            if not self._auto_run_active:
                self._reset_execution_view()
        except Exception as exc:
            show_error(self, "task詳細読込エラー", exc)

    def on_show_next(self) -> None:
        try:
            repo_path = require_repo_path(self)
            handle_repo_changed(self, repo_path)
            task_id = require_selected_task_id(self)

            result = ShowNextUseCase().execute(repo_path=repo_path, task_id=task_id)
            self._apply_show_next_result(result)

            append_log(
                self,
                "[INFO] show-next completed: "
                f"task_id={task_id}, role={result['role']}, cycle={result['cycle']}",
            )
        except Exception as exc:
            show_error(self, "show-next エラー", exc)

    def on_run_claude_step(self) -> None:
        try:
            if self._auto_run_active:
                append_log(self, "[INFO] auto run is already active.")
                return

            repo_path = require_repo_path(self)
            handle_repo_changed(self, repo_path)
            task_id = require_selected_task_id(self)

            self._reset_execution_view()
            self._set_execution_state("starting")
            self._set_execution_step("preparing")
            self._set_execution_role(self.current_task_next_role_edit.text().strip())
            self._set_execution_cycle(self.current_task_cycle_edit.text().strip())

            self._set_auto_run_controls_enabled(False)
            self._auto_run_active = True

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
            self._set_auto_run_controls_enabled(True)
            self._auto_run_active = False
            show_error(self, "Claude自動実行エラー", exc)

    def on_validate_report(self) -> None:
        try:
            repo_path = require_repo_path(self)
            handle_repo_changed(self, repo_path)
            task_id = require_selected_task_id(self)
            role = self.detail_next_role.text().strip()

            if not role or role == "none":
                raise ValueError("next_role is empty or none.")

            result = ValidateReportUseCase().execute(
                repo_path=repo_path,
                task_id=task_id,
                role=role,
            )

            text = (
                f"valid: {result['valid']}\n"
                f"role: {result['role']}\n"
                f"cycle: {result['cycle']}\n"
                f"report_path: {result['report_path']}"
            )
            self.validation_result_edit.setPlainText(text)

            append_log(
                self,
                "[INFO] validate-report success: "
                f"task_id={task_id}, role={result['role']}, cycle={result['cycle']}",
            )
        except Exception as exc:
            self.validation_result_edit.setPlainText(
                f"ERROR\n{type(exc).__name__}: {exc}"
            )
            show_error(self, "validate-report エラー", exc)

    def on_advance_task(self) -> None:
        try:
            repo_path = require_repo_path(self)
            handle_repo_changed(self, repo_path)
            task_id = require_selected_task_id(self)

            result = AdvanceTaskUseCase().execute(repo_path=repo_path, task_id=task_id)

            append_log(
                self,
                "[INFO] advance completed: "
                f"task_id={task_id}, "
                f"status={result['status']}, "
                f"current={result['current_stage']}, "
                f"next={result['next_role']}, "
                f"cycle={result['cycle']}",
            )

            load_selected_task_detail(self, task_id)
            refresh_task_list(self)

        except Exception as exc:
            show_error(self, "advance エラー", exc)

    def on_reload_selected_task(self) -> None:
        try:
            repo_path = require_repo_path(self)
            handle_repo_changed(self, repo_path)
            task_id = require_selected_task_id(self)

            load_selected_task_detail(self, task_id)

            if self._last_prompt_path:
                prompt_text = read_text_file_if_exists(self._last_prompt_path)
                self.prompt_text_edit.setPlainText(prompt_text)
                self.current_prompt_path_edit.setText(self._last_prompt_path)

            if self._last_output_json_path:
                self.current_output_json_path_edit.setText(self._last_output_json_path)
                self.output_path_detail_edit.setPlainText(self._last_output_json_path)

            append_log(self, f"[INFO] selected task reloaded: {task_id}")
        except Exception as exc:
            show_error(self, "再読込エラー", exc)

    def _apply_show_next_result(self, result: dict) -> str:
        prompt_path = str(result["prompt_path"])
        output_json_path = str(result["output_json_path"])
        prompt_text = read_text_file_if_exists(prompt_path)

        self._last_prompt_path = prompt_path
        self._last_output_json_path = output_json_path

        self.current_prompt_path_edit.setText(prompt_path)
        self.current_output_json_path_edit.setText(output_json_path)
        self.prompt_text_edit.setPlainText(prompt_text)
        self.output_path_detail_edit.setPlainText(output_json_path)

        return prompt_text

    def _reset_execution_view(self) -> None:
        self.execution_status_edit.setText("idle")
        self.execution_step_edit.setText("waiting")
        self.execution_role_edit.clear()
        self.execution_cycle_edit.clear()
        self.claude_monitor_edit.clear()

    def _set_execution_state(self, text: str) -> None:
        self.execution_status_edit.setText(text)

    def _set_execution_step(self, text: str) -> None:
        self.execution_step_edit.setText(text)

    def _set_execution_role(self, text: str) -> None:
        self.execution_role_edit.setText(text)

    def _set_execution_cycle(self, text: str) -> None:
        self.execution_cycle_edit.setText(text)

    def _append_monitor_message(self, message: str) -> None:
        self.claude_monitor_edit.appendPlainText(message)

    def _set_auto_run_controls_enabled(self, enabled: bool) -> None:
        self.repo_path_edit.setEnabled(enabled)
        self.btn_repo_browse.setEnabled(enabled)
        self.btn_check_init.setEnabled(enabled)
        self.btn_init_project.setEnabled(enabled)

        self.task_title_edit.setEnabled(enabled)
        self.task_desc_edit.setEnabled(enabled)
        self.context_files_edit.setEnabled(enabled)
        self.constraints_edit.setEnabled(enabled)
        self.btn_create_task.setEnabled(enabled)

        self.task_list_widget.setEnabled(enabled)
        self.btn_refresh_tasks.setEnabled(enabled)

        self.btn_run_claude_step.setEnabled(enabled)
        self.btn_show_next.setEnabled(enabled)
        self.btn_validate.setEnabled(enabled)
        self.btn_advance.setEnabled(enabled)
        self.btn_reload_selected.setEnabled(enabled)

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

    def _on_worker_monitor_message(self, message: str) -> None:
        self._append_monitor_message(message)

    def _on_worker_log_message(self, message: str) -> None:
        append_log(self, message)

    def _on_worker_show_next_ready(self, result: object) -> None:
        if isinstance(result, dict):
            self._apply_show_next_result(result)

    def _on_worker_validation_ready(self, text: str) -> None:
        self.validation_result_edit.setPlainText(text)

    def _on_worker_task_detail_requested(self, task_id: str) -> None:
        try:
            load_selected_task_detail(self, task_id)
        except Exception as exc:
            show_error(self, "task詳細更新エラー", exc)

    def _on_worker_task_list_refresh_requested(self) -> None:
        try:
            refresh_task_list(self)
        except Exception as exc:
            show_error(self, "task一覧更新エラー", exc)

    def _on_worker_error(self, title: str, message: str) -> None:
        self._set_execution_state("failed")
        self._set_execution_step("stopped")
        self._append_monitor_message(message)
        append_log(self, f"[ERROR] {message}")
        show_error(self, title, RuntimeError(message))

    def _on_worker_completed(self, task_id: str, cycle: str) -> None:
        self._set_execution_state("completed")
        self._set_execution_step("stopped")
        self._set_execution_role("none")
        self._set_execution_cycle(cycle)
        self._append_monitor_message(f"task completed: {task_id}")
        append_log(self, f"[INFO] task completed: {task_id}, cycle={cycle}")

    def _on_auto_run_thread_finished(self) -> None:
        self._auto_run_active = False
        self._set_auto_run_controls_enabled(True)
        self._auto_run_worker = None
        self._auto_run_thread = None
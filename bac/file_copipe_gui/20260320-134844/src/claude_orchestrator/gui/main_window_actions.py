# src\claude_orchestrator\gui\main_window_actions.py
from __future__ import annotations

import json
from pathlib import Path

from PySide6.QtCore import Qt

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
from claude_orchestrator.gui.dialog_helpers import append_log, show_error, show_info
from claude_orchestrator.gui.state_helpers import (
    handle_repo_changed,
    load_selected_task_detail,
    parse_multiline_list,
    read_text_file_if_exists,
    refresh_task_list,
    require_repo_path,
    require_selected_task_id,
)
from claude_orchestrator.infrastructure.project_paths import ProjectPaths


class MainWindowActionsMixin:
    _ROLE_ORDER = ["task_router", "implementer", "reviewer", "director"]

    def on_browse_repo(self) -> None:
        from PySide6.QtWidgets import QFileDialog

        selected = QFileDialog.getExistingDirectory(self, "対象 repo を選択")
        if not selected:
            return

        self.repo_path_edit.setText(selected)
        handle_repo_changed(self, selected)

        if not self._auto_run_active:
            self._reset_execution_view()
        if not self._planner_active:
            self._reset_planner_view()

        refresh_task_list(self)
        self._load_remote_session_info_safe()

    def on_repo_path_edited(self) -> None:
        handle_repo_changed(self, self.repo_path_edit.text().strip())

        if not self._auto_run_active:
            self._reset_execution_view()
        if not self._planner_active:
            self._reset_planner_view()

        refresh_task_list(self)
        self._load_remote_session_info_safe()

    def on_check_initialized(self) -> None:
        try:
            repo_path = require_repo_path(self)
            handle_repo_changed(self, repo_path)

            project_paths = ProjectPaths(target_repo=Path(repo_path))
            project_paths.ensure_initialized()

            append_log(self, f"[INFO] initialized repo confirmed: {project_paths.root}")
            refresh_task_list(self)
            self._load_remote_session_info_safe()
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
            self._load_remote_session_info_safe()
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
            if not self._planner_active:
                self._reset_planner_view()
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
            task_id = str(items[0].data(Qt.UserRole))
            load_selected_task_detail(self, task_id)

            if not self._auto_run_active:
                self._load_task_inbox_logs(task_id)

            if not self._planner_active:
                self._load_existing_planner_data(task_id)
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

            self._load_existing_planner_data(task_id)
            self._load_remote_session_info_safe()
            append_log(self, f"[INFO] selected task reloaded: {task_id}")
        except Exception as exc:
            show_error(self, "再読込エラー", exc)

    def _load_task_inbox_logs(self, task_id: str) -> None:
        self.execution_status_edit.setText("idle")
        self.execution_step_edit.setText("waiting")
        self.execution_role_edit.clear()
        self.execution_cycle_edit.clear()
        self.claude_monitor_edit.clear()

        repo_path = self.repo_path_edit.text().strip()
        if not repo_path:
            return

        inbox_dir = Path(repo_path) / ".claude_orchestrator" / "tasks" / task_id / "inbox"
        if not inbox_dir.exists():
            return

        reports = []
        for json_path in inbox_dir.glob("*.json"):
            try:
                data = json.loads(json_path.read_text(encoding="utf-8"))
                reports.append(data)
            except Exception:
                continue

        def _role_sort_key(report: dict) -> tuple:
            role = report.get("role", "")
            try:
                order = self._ROLE_ORDER.index(role)
            except ValueError:
                order = len(self._ROLE_ORDER)
            return (report.get("cycle", 1), order)

        reports.sort(key=_role_sort_key)

        for report in reports:
            role = report.get("role", "unknown")
            cycle = report.get("cycle", "?")
            status = report.get(
                "status",
                report.get("decision", report.get("final_action", "?")),
            )
            summary = report.get("summary", "")

            self._append_monitor_message(
                f"=== {role}  cycle={cycle}  status={status} ==="
            )
            if summary:
                self._append_monitor_message(summary)
# src\claude_orchestrator\gui\main_window.py
from __future__ import annotations

from pathlib import Path

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
from claude_orchestrator.infrastructure.project_paths import ProjectPaths

from claude_orchestrator.gui.claude_runner import ClaudeRunResult, run_claude_print_mode
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


class MainWindow(QMainWindow):
    def __init__(self) -> None:
        super().__init__()

        self.setWindowTitle("Claude Orchestrator GUI MVP")
        self.resize(1600, 950)

        self._last_prompt_path: str = ""
        self._last_output_json_path: str = ""
        self._current_task_id: str = ""
        self._last_repo_path: str = ""

        build_main_window_ui(self)
        connect_main_window_signals(self)
        apply_initial_state(self)

    def on_browse_repo(self) -> None:
        from PySide6.QtWidgets import QFileDialog

        selected = QFileDialog.getExistingDirectory(self, "対象 repo を選択")
        if not selected:
            return
        self.repo_path_edit.setText(selected)
        handle_repo_changed(self, selected)

    def on_repo_path_edited(self) -> None:
        handle_repo_changed(self, self.repo_path_edit.text().strip())

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
            repo_path = require_repo_path(self)
            handle_repo_changed(self, repo_path)
            task_id = require_selected_task_id(self)

            show_next_result = ShowNextUseCase().execute(repo_path=repo_path, task_id=task_id)
            prompt_text = self._apply_show_next_result(show_next_result)

            role = str(show_next_result["role"])
            cycle = int(show_next_result["cycle"])
            output_json_path = str(show_next_result["output_json_path"])

            if not prompt_text.strip():
                raise ValueError("prompt text is empty.")

            append_log(
                self,
                "[INFO] claude step started: "
                f"task_id={task_id}, role={role}, cycle={cycle}",
            )
            append_log(self, f"[INFO] claude cwd: {Path(repo_path).resolve()}")

            claude_result = run_claude_print_mode(
                repo_path=repo_path,
                prompt_text=prompt_text,
            )
            self._log_claude_result(claude_result)

            if claude_result.returncode != 0:
                raise RuntimeError(
                    "claude command failed. "
                    f"returncode={claude_result.returncode}"
                )

            self._ensure_output_json_exists(output_json_path)
            append_log(self, f"[INFO] report json saved: {output_json_path}")

            load_selected_task_detail(self, task_id)
            refresh_task_list(self)

        except Exception as exc:
            show_error(self, "Claude実行エラー", exc)

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
        self.validation_result_edit.clear()

        return prompt_text

    def _log_claude_result(self, result: ClaudeRunResult) -> None:
        append_log(
            self,
            "[INFO] claude finished: "
            f"returncode={result.returncode}, command={' '.join(result.command)}",
        )

        stdout_text = result.stdout.strip()
        stderr_text = result.stderr.strip()

        if stdout_text:
            append_log(self, "[INFO] claude stdout:")
            append_log(self, stdout_text)

        if stderr_text:
            append_log(self, "[INFO] claude stderr:")
            append_log(self, stderr_text)

    def _ensure_output_json_exists(self, output_json_path: str) -> None:
        output_path = Path(output_json_path)
        if not output_path.exists():
            raise FileNotFoundError(f"Report file not found: {output_path}")
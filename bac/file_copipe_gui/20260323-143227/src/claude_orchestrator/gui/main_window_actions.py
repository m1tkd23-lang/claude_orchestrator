# src\claude_orchestrator\gui\main_window_actions.py
from __future__ import annotations

from pathlib import Path

from claude_orchestrator.application.usecases.advance_task_usecase import (
    AdvanceTaskUseCase,
)
from claude_orchestrator.application.usecases.show_next_usecase import (
    ShowNextUseCase,
)
from claude_orchestrator.application.usecases.validate_report_usecase import (
    ValidateReportUseCase,
)
from claude_orchestrator.gui.dialog_helpers import append_log, show_error, show_info
from claude_orchestrator.gui.state_helpers import (
    get_display_target_task_id,
    get_repo_path,
    handle_repo_changed,
    load_selected_task_detail,
    normalize_repo_path,
    read_text_file_if_exists,
    refresh_task_list,
    require_repo_path,
    set_active_pipeline_task,
    set_selected_task,
)


class MainWindowActionsMixin:
    def on_refresh_tasks(self) -> None:
        try:
            repo_path = require_repo_path(self)
            handle_repo_changed(self, repo_path)
            refresh_task_list(self)

            target_task_id = get_display_target_task_id(self)
            if target_task_id:
                load_selected_task_detail(self, target_task_id)

            append_log(self, "[INFO] task list refreshed.")
        except Exception as exc:
            show_error(self, "task list refresh error", exc)

    def on_task_selected(self) -> None:
        try:
            items = self.task_list_widget.selectedItems()
            if not items:
                return

            item = items[0]
            task_id = str(item.data(item.UserRole) or "").strip()
            if not task_id:
                return

            set_selected_task(self, task_id)
            if not bool(getattr(self, "_auto_run_active", False)) \
               and not bool(getattr(self, "_planner_active", False)) \
               and not bool(getattr(self, "_plan_director_active", False)) \
               and not bool(getattr(self, "_waiting_next_task_approval", False)):
                self._active_pipeline_task_id = ""

            load_selected_task_detail(self, task_id)
            self._load_task_inbox_logs(task_id)
            self._load_existing_planner_data(task_id)
            self._refresh_pipeline_controls()
            self._refresh_pipeline_tab()
            append_log(self, f"[INFO] task detail loaded: {task_id}")
        except Exception as exc:
            show_error(self, "task detail load error", exc)

    def on_reload_selected_task(self) -> None:
        try:
            repo_path = require_repo_path(self)
            handle_repo_changed(self, repo_path)

            task_id = get_display_target_task_id(self)
            if not task_id:
                raise ValueError("task を選択してください。")

            refresh_task_list(self)
            load_selected_task_detail(self, task_id)
            self._load_task_inbox_logs(task_id)
            self._load_existing_planner_data(task_id)
            self._refresh_pipeline_controls()
            self._refresh_pipeline_tab()
            append_log(self, f"[INFO] task detail reloaded: {task_id}")
        except Exception as exc:
            show_error(self, "task reload error", exc)

    def on_show_next(self) -> None:
        try:
            repo_path = require_repo_path(self)
            handle_repo_changed(self, repo_path)
            task_id = get_display_target_task_id(self)
            if not task_id:
                raise ValueError("task を選択してください。")

            result = ShowNextUseCase().execute(
                repo_path=repo_path,
                task_id=task_id,
            )
            prompt_path = str(result["prompt_path"])
            output_json_path = str(result["output_json_path"])

            self.current_prompt_path_edit.setText(prompt_path)
            self.current_output_json_path_edit.setText(output_json_path)
            self.prompt_text_edit.setPlainText(read_text_file_if_exists(prompt_path))
            self.output_path_detail_edit.setPlainText(output_json_path)

            set_active_pipeline_task(self, task_id)
            self._set_execution_state("ready")
            self._set_execution_step("show-next")
            self._set_execution_role(str(result.get("role", "")))
            self._set_execution_cycle(str(result.get("cycle", "")))
            self._append_monitor_message("show-next completed")
            self._append_monitor_message(
                f"role / cycle / revision: "
                f"{result.get('role', '')} / {result.get('cycle', '')} / {result.get('revision', '')}"
            )
            self._refresh_pipeline_controls()
            self._refresh_pipeline_tab()

            append_log(
                self,
                "[INFO] show-next completed: "
                f"task_id={task_id}, role={result.get('role', '')}, cycle={result.get('cycle', '')}",
            )
        except Exception as exc:
            show_error(self, "show-next error", exc)

    def on_validate_report(self) -> None:
        try:
            repo_path = require_repo_path(self)
            handle_repo_changed(self, repo_path)
            task_id = get_display_target_task_id(self)
            if not task_id:
                raise ValueError("task を選択してください。")

            show_next_result = ShowNextUseCase().execute(
                repo_path=repo_path,
                task_id=task_id,
            )
            role = str(show_next_result["role"])
            cycle = int(show_next_result["cycle"])
            revision = int(show_next_result.get("revision", 1))

            result = ValidateReportUseCase().execute(
                repo_path=repo_path,
                task_id=task_id,
                role=role,
                expected_cycle=cycle,
                expected_revision=revision,
            )
            text = (
                f"valid: {result['valid']}\n"
                f"role: {result['role']}\n"
                f"cycle: {result['cycle']}\n"
                f"revision: {result['revision']}\n"
                f"report_path: {result['report_path']}"
            )
            self.output_path_detail_edit.setPlainText(text)

            set_active_pipeline_task(self, task_id)
            self._set_execution_state("validated")
            self._set_execution_step("validate-report")
            self._set_execution_role(role)
            self._set_execution_cycle(str(cycle))
            self._append_monitor_message("validate success")
            self._refresh_pipeline_controls()
            self._refresh_pipeline_tab()

            append_log(
                self,
                "[INFO] validate-report success: "
                f"task_id={task_id}, role={role}, cycle={cycle}, revision={revision}",
            )
        except Exception as exc:
            show_error(self, "validate-report error", exc)

    def on_advance_task(self) -> None:
        try:
            repo_path = require_repo_path(self)
            handle_repo_changed(self, repo_path)
            task_id = get_display_target_task_id(self)
            if not task_id:
                raise ValueError("task を選択してください。")

            show_next_result = ShowNextUseCase().execute(
                repo_path=repo_path,
                task_id=task_id,
            )
            role = str(show_next_result["role"])
            cycle = int(show_next_result["cycle"])
            revision = int(show_next_result.get("revision", 1))

            result = AdvanceTaskUseCase().execute(
                repo_path=repo_path,
                task_id=task_id,
                expected_role=role,
                expected_cycle=cycle,
                expected_revision=revision,
            )

            refresh_task_list(self)
            set_active_pipeline_task(self, task_id)
            load_selected_task_detail(self, task_id)
            self._load_task_inbox_logs(task_id)
            self._load_existing_planner_data(task_id)

            self._set_execution_state(str(result.get("status", "")))
            self._set_execution_step("advance")
            self._set_execution_role(str(result.get("current_stage", "")))
            self._set_execution_cycle(str(result.get("cycle", "")))
            self._append_monitor_message(
                "advanced to next role: "
                f"{result.get('next_role', '')} "
                f"(status={result.get('status', '')}, "
                f"cycle={result.get('cycle', '')}, "
                f"revision={result.get('revision', '')})"
            )
            self._refresh_pipeline_controls()
            self._refresh_pipeline_tab()

            append_log(
                self,
                "[INFO] advance completed: "
                f"task_id={task_id}, "
                f"status={result.get('status', '')}, "
                f"current={result.get('current_stage', '')}, "
                f"next={result.get('next_role', '')}, "
                f"cycle={result.get('cycle', '')}, "
                f"revision={result.get('revision', '')}",
            )
        except Exception as exc:
            show_error(self, "advance error", exc)

    def on_create_task(self) -> None:
        try:
            refresh_task_list(self)
            target_task_id = get_display_target_task_id(self)
            if target_task_id:
                set_active_pipeline_task(self, target_task_id)
                load_selected_task_detail(self, target_task_id)
                self._load_task_inbox_logs(target_task_id)
                self._load_existing_planner_data(target_task_id)
                self._refresh_pipeline_controls()
                self._refresh_pipeline_tab()
        except Exception as exc:
            show_error(self, "task create follow error", exc)

    def _load_task_inbox_logs(self, task_id: str) -> None:
        repo_path = normalize_repo_path(get_repo_path(self))
        if not repo_path:
            return

        task_dir = (
            Path(repo_path)
            / ".claude_orchestrator"
            / "tasks"
            / str(task_id).strip()
            / "inbox"
        )
        if not task_dir.exists():
            return

        report_paths = sorted(task_dir.glob("*_report_v*.json"))
        if not report_paths:
            return

        log_lines: list[str] = []
        for report_path in report_paths:
            log_lines.append(f"=== {report_path.name} ===")
            try:
                log_lines.append(report_path.read_text(encoding="utf-8"))
            except Exception as exc:
                log_lines.append(f"[READ ERROR] {type(exc).__name__}: {exc}")
            log_lines.append("")

        self.log_edit.setPlainText("\n".join(log_lines).strip())
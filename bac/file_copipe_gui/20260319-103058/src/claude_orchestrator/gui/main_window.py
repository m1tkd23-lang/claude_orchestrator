# src\claude_orchestrator\gui\main_window.py
from __future__ import annotations

import json
from pathlib import Path

from PySide6.QtCore import QThread, Qt
from PySide6.QtWidgets import QMainWindow, QListWidgetItem

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
from claude_orchestrator.gui.planner_helpers import (
    build_proposal_detail_text,
    build_proposal_list_text,
    proposal_to_task_form_fields,
)
from claude_orchestrator.gui.planner_worker import PlannerWorker
from claude_orchestrator.gui.proposal_state_store import ProposalStateStore
from claude_orchestrator.gui.state_helpers import (
    apply_initial_state,
    clear_planner_area,
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
from claude_orchestrator.infrastructure.planner_runtime import PlannerRuntime
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

        self._planner_thread: QThread | None = None
        self._planner_worker: PlannerWorker | None = None
        self._planner_active: bool = False

        self._planner_report: dict | None = None
        self._planner_state_store: ProposalStateStore | None = None
        self._planner_selected_proposal_id: str = ""

        self._default_reference_doc_paths = [
            r"docs\Claude Orchestrator GUI 開発記録 & 次工程指示書.md",
            r"docs\workflow_rules.md",
            r"docs\planner_v1_仕様書.md",
        ]

        build_main_window_ui(self)
        connect_main_window_signals(self)
        apply_initial_state(self)
        self._reset_execution_view()
        self._reset_planner_view()

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

    def on_repo_path_edited(self) -> None:
        handle_repo_changed(self, self.repo_path_edit.text().strip())
        if not self._auto_run_active:
            self._reset_execution_view()
        if not self._planner_active:
            self._reset_planner_view()

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

            self._load_existing_planner_data(task_id)
            append_log(self, f"[INFO] selected task reloaded: {task_id}")
        except Exception as exc:
            show_error(self, "再読込エラー", exc)

    def on_generate_next_tasks(self) -> None:
        try:
            if self._planner_active:
                append_log(self, "[INFO] planner generation is already active.")
                return

            repo_path = require_repo_path(self)
            handle_repo_changed(self, repo_path)
            source_task_id = require_selected_task_id(self)

            self._reset_planner_view()
            self._planner_active = True
            self._set_planner_controls_enabled(False)

            self._planner_thread = QThread(self)
            self._planner_worker = PlannerWorker(
                repo_path=repo_path,
                source_task_id=source_task_id,
                reference_doc_paths=self._default_reference_doc_paths,
            )
            self._planner_worker.moveToThread(self._planner_thread)

            self._planner_thread.started.connect(self._planner_worker.run)
            self._planner_worker.log_message.connect(self._on_planner_log_message)
            self._planner_worker.result_ready.connect(self._on_planner_result_ready)
            self._planner_worker.error_signal.connect(self._on_planner_error)
            self._planner_worker.finished.connect(self._planner_thread.quit)
            self._planner_worker.finished.connect(self._planner_worker.deleteLater)
            self._planner_thread.finished.connect(self._on_planner_thread_finished)
            self._planner_thread.finished.connect(self._planner_thread.deleteLater)

            self._planner_thread.start()

        except Exception as exc:
            self._planner_active = False
            self._set_planner_controls_enabled(True)
            show_error(self, "次タスク案作成エラー", exc)

    def on_planner_proposal_selected(self) -> None:
        items = self.planner_proposal_list_widget.selectedItems()
        if not items:
            self._planner_selected_proposal_id = ""
            self.planner_proposal_detail_edit.clear()
            self._update_planner_action_buttons()
            return

        proposal_id = str(items[0].data(Qt.UserRole))
        self._planner_selected_proposal_id = proposal_id
        proposal = self._get_selected_proposal_dict()
        if proposal is None:
            self.planner_proposal_detail_edit.clear()
            self._update_planner_action_buttons()
            return

        state = self._get_selected_proposal_state(proposal_id)
        self.planner_proposal_detail_edit.setPlainText(
            build_proposal_detail_text(proposal, state)
        )
        self._update_planner_action_buttons()

    def on_accept_proposal(self) -> None:
        try:
            proposal = self._require_selected_proposal_dict()
            proposal_id = str(proposal["proposal_id"])

            if self._planner_state_store is None:
                raise ValueError("planner state store is not initialized.")

            self._planner_state_store.set_state(proposal_id, "accepted")
            fields = proposal_to_task_form_fields(proposal)

            self.task_title_edit.setText(fields["title"])
            self.task_desc_edit.setPlainText(fields["description"])
            self.context_files_edit.setPlainText(fields["context_files_text"])
            self.constraints_edit.setPlainText(fields["constraints_text"])

            self.main_tabs.setCurrentIndex(0)
            self._refresh_planner_list_from_current_report()
            append_log(self, f"[INFO] planner proposal accepted: {proposal_id}")
        except Exception as exc:
            show_error(self, "planner採用エラー", exc)

    def on_reject_proposal(self) -> None:
        try:
            proposal = self._require_selected_proposal_dict()
            proposal_id = str(proposal["proposal_id"])

            if self._planner_state_store is None:
                raise ValueError("planner state store is not initialized.")

            self._planner_state_store.set_state(proposal_id, "rejected")
            self._refresh_planner_list_from_current_report()
            append_log(self, f"[INFO] planner proposal rejected: {proposal_id}")
        except Exception as exc:
            show_error(self, "planner否決エラー", exc)

    def on_defer_proposal(self) -> None:
        try:
            proposal = self._require_selected_proposal_dict()
            proposal_id = str(proposal["proposal_id"])

            if self._planner_state_store is None:
                raise ValueError("planner state store is not initialized.")

            self._planner_state_store.set_state(proposal_id, "deferred")
            self._refresh_planner_list_from_current_report()
            append_log(self, f"[INFO] planner proposal deferred: {proposal_id}")
        except Exception as exc:
            show_error(self, "planner保留エラー", exc)

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

    _ROLE_ORDER = ["task_router", "implementer", "reviewer", "director"]

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

        def _role_sort_key(r: dict) -> tuple:
            role = r.get("role", "")
            try:
                order = self._ROLE_ORDER.index(role)
            except ValueError:
                order = len(self._ROLE_ORDER)
            return (r.get("cycle", 1), order)

        reports.sort(key=_role_sort_key)

        for report in reports:
            role = report.get("role", "unknown")
            cycle = report.get("cycle", "?")
            status = report.get("status", report.get("decision", report.get("final_action", "?")))
            summary = report.get("summary", "")
            self._append_monitor_message(
                f"=== {role}  cycle={cycle}  status={status} ==="
            )
            if summary:
                self._append_monitor_message(summary)

    def _reset_planner_view(self) -> None:
        clear_planner_area(self)
        self._planner_report = None
        self._planner_state_store = None
        self._planner_selected_proposal_id = ""
        self._update_planner_action_buttons()

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
        self.btn_generate_next_tasks.setEnabled(enabled and not self._planner_active)

    def _set_planner_controls_enabled(self, enabled: bool) -> None:
        self.btn_generate_next_tasks.setEnabled(enabled and not self._auto_run_active)
        self.planner_proposal_list_widget.setEnabled(enabled)
        self._update_planner_action_buttons(base_enabled=enabled)

    def _update_planner_action_buttons(self, base_enabled: bool = True) -> None:
        has_selection = bool(self._planner_selected_proposal_id)
        enabled = base_enabled and has_selection and not self._planner_active and not self._auto_run_active

        self.btn_accept_proposal.setEnabled(enabled)
        self.btn_reject_proposal.setEnabled(enabled)
        self.btn_defer_proposal.setEnabled(enabled)

    def _load_existing_planner_data(self, task_id: str) -> None:
        self._reset_planner_view()

        try:
            repo_path = require_repo_path(self)
            runtime = PlannerRuntime(
                target_repo=Path(repo_path).resolve(),
                source_task_id=task_id,
            )
            state_json = runtime.load_source_state_json()
            cycle = int(state_json["cycle"])
            report_path = runtime.get_report_path(cycle)
            if not report_path.exists():
                return

            planner_report = json_load_path(report_path)
            self._planner_report = planner_report
            self._planner_state_store = ProposalStateStore(
                repo_path=repo_path,
                source_task_id=task_id,
                cycle=cycle,
            )
            self._refresh_planner_list_from_current_report()
        except Exception:
            self._reset_planner_view()

    def _refresh_planner_list_from_current_report(self) -> None:
        self.planner_proposal_list_widget.clear()
        self.planner_proposal_detail_edit.clear()
        self._planner_selected_proposal_id = ""

        if not self._planner_report:
            self.planner_summary_edit.clear()
            self._update_planner_action_buttons()
            return

        summary = str(self._planner_report.get("summary", ""))
        self.planner_summary_edit.setPlainText(summary)

        state_map = {}
        if self._planner_state_store is not None:
            state_map = self._planner_state_store.get_state_map()

        for proposal in self._planner_report.get("proposals", []):
            proposal_id = str(proposal.get("proposal_id", ""))
            state = state_map.get(proposal_id, "proposed")

            item = QListWidgetItem(build_proposal_list_text(proposal, state))
            item.setData(Qt.UserRole, proposal_id)
            self.planner_proposal_list_widget.addItem(item)

        self._update_planner_action_buttons()

    def _get_selected_proposal_dict(self) -> dict | None:
        if not self._planner_report or not self._planner_selected_proposal_id:
            return None

        for proposal in self._planner_report.get("proposals", []):
            if str(proposal.get("proposal_id")) == self._planner_selected_proposal_id:
                return proposal
        return None

    def _require_selected_proposal_dict(self) -> dict:
        proposal = self._get_selected_proposal_dict()
        if proposal is None:
            raise ValueError("planner proposal is not selected.")
        return proposal

    def _get_selected_proposal_state(self, proposal_id: str) -> str:
        if self._planner_state_store is None:
            return "proposed"
        return self._planner_state_store.get_state_map().get(proposal_id, "proposed")

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
        self._update_planner_action_buttons()

    def _on_planner_log_message(self, message: str) -> None:
        append_log(self, message)

    def _on_planner_result_ready(self, result: object) -> None:
        if not isinstance(result, dict):
            return

        planner_report = result.get("planner_report")
        if not isinstance(planner_report, dict):
            raise ValueError("planner_report is invalid.")

        repo_path = require_repo_path(self)
        source_task_id = str(result["source_task_id"])
        cycle = int(result["cycle"])

        self._planner_report = planner_report
        self._planner_state_store = ProposalStateStore(
            repo_path=repo_path,
            source_task_id=source_task_id,
            cycle=cycle,
        )
        self._planner_state_store.initialize_from_report(planner_report)
        self._refresh_planner_list_from_current_report()

        prompt_path = str(result["prompt_path"])
        output_json_path = str(result["output_json_path"])
        self.current_prompt_path_edit.setText(prompt_path)
        self.current_output_json_path_edit.setText(output_json_path)
        self.prompt_text_edit.setPlainText(read_text_file_if_exists(prompt_path))
        self.output_path_detail_edit.setPlainText(output_json_path)

        append_log(self, f"[INFO] planner report saved: {output_json_path}")

    def _on_planner_error(self, title: str, message: str) -> None:
        append_log(self, f"[ERROR] {message}")
        show_error(self, title, RuntimeError(message))

    def _on_planner_thread_finished(self) -> None:
        self._planner_active = False
        self._planner_worker = None
        self._planner_thread = None
        self._set_planner_controls_enabled(True)

        if self._current_task_id:
            self._load_existing_planner_data(self._current_task_id)

    def closeEvent(self, event) -> None:  # type: ignore[override]
        if self._auto_run_thread is not None and self._auto_run_thread.isRunning():
            self._auto_run_thread.quit()
            self._auto_run_thread.wait(1000)

        if self._planner_thread is not None and self._planner_thread.isRunning():
            self._planner_thread.quit()
            self._planner_thread.wait(1000)

        super().closeEvent(event)


def json_load_path(path: Path) -> dict:
    with path.open("r", encoding="utf-8") as f:
        return json.load(f)
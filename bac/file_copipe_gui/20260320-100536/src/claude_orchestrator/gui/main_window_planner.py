# src\claude_orchestrator\gui\main_window_planner.py
from __future__ import annotations

import json
from pathlib import Path

from PySide6.QtCore import Qt
from PySide6.QtWidgets import QListWidgetItem

from claude_orchestrator.application.usecases.create_task_from_proposal_usecase import (
    CreateTaskFromProposalUseCase,
)
from claude_orchestrator.gui.dialog_helpers import append_log, show_error, show_info
from claude_orchestrator.gui.planner_helpers import (
    build_proposal_detail_text,
    build_proposal_list_text,
    proposal_to_task_form_fields,
)
from claude_orchestrator.gui.planner_worker import PlannerWorker
from claude_orchestrator.gui.proposal_state_store import ProposalStateStore
from claude_orchestrator.gui.state_helpers import (
    clear_planner_area,
    handle_repo_changed,
    load_selected_task_detail,
    read_text_file_if_exists,
    refresh_task_list,
    require_repo_path,
    require_selected_task_id,
)
from claude_orchestrator.infrastructure.planner_runtime import PlannerRuntime


class MainWindowPlannerMixin:
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

            from PySide6.QtCore import QThread

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

    def on_create_task_from_proposal(self) -> None:
        try:
            if self._auto_run_active:
                raise ValueError("auto run active中は proposal から task 作成できません。")
            if self._planner_active:
                raise ValueError("planner generation中は proposal から task 作成できません。")

            repo_path = require_repo_path(self)
            handle_repo_changed(self, repo_path)
            source_task_id = require_selected_task_id(self)
            proposal = self._require_selected_proposal_dict()
            proposal_id = str(proposal["proposal_id"]).strip()

            result = CreateTaskFromProposalUseCase().execute(
                repo_path=repo_path,
                source_task_id=source_task_id,
                proposal_id=proposal_id,
            )

            created_task_id = str(result["created_task_id"])
            self._current_task_id = created_task_id

            refresh_task_list(self)
            load_selected_task_detail(self, created_task_id)

            if not self._auto_run_active:
                self._reset_execution_view()
            if not self._planner_active:
                self._load_existing_planner_data(source_task_id)

            append_log(
                self,
                "[INFO] task created from proposal: "
                f"source_task_id={source_task_id}, "
                f"proposal_id={proposal_id}, "
                f"created_task_id={created_task_id}",
            )
            show_info(
                self,
                "task 作成完了",
                "proposal から task を作成しました。\n"
                f"source_task_id: {source_task_id}\n"
                f"proposal_id: {proposal_id}\n"
                f"created_task_id: {created_task_id}",
            )
            self.main_tabs.setCurrentIndex(0)
        except Exception as exc:
            show_error(self, "proposal から task 作成エラー", exc)

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

    def _reset_planner_view(self) -> None:
        clear_planner_area(self)
        self._planner_report = None
        self._planner_state_store = None
        self._planner_selected_proposal_id = ""
        self._update_planner_action_buttons()

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

            planner_report = self._json_load_path(report_path)
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

    @staticmethod
    def _json_load_path(path: Path) -> dict:
        with path.open("r", encoding="utf-8") as file:
            return json.load(file)
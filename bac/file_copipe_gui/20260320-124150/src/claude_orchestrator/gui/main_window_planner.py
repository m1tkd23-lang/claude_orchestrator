# src\claude_orchestrator\gui\main_window_planner.py
from __future__ import annotations

import json
from pathlib import Path

from PySide6.QtCore import Qt
from PySide6.QtWidgets import QListWidgetItem

from claude_orchestrator.application.usecases.create_task_from_plan_director_usecase import (
    CreateTaskFromPlanDirectorUseCase,
)
from claude_orchestrator.application.usecases.create_task_from_proposal_usecase import (
    CreateTaskFromProposalUseCase,
)
from claude_orchestrator.gui.dialog_helpers import append_log, show_error, show_info
from claude_orchestrator.gui.plan_director_worker import PlanDirectorWorker
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
            self._start_planner_generation(auto_run_plan_director=False)
        except Exception as exc:
            show_error(self, "次タスク案作成エラー", exc)

    def on_run_plan_director(self) -> None:
        try:
            self._start_plan_director_run()
        except Exception as exc:
            show_error(self, "plan_director 実行エラー", exc)

    def on_planner_role_changed(self) -> None:
        self._planner_role = self._get_current_planner_role()
        if self._current_task_id:
            self._load_existing_planner_data(self._current_task_id)

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
            append_log(
                self,
                "[INFO] planner proposal accepted: "
                f"proposal_id={proposal_id}, "
                f"planner_role={self._get_current_planner_role()}",
            )
        except Exception as exc:
            show_error(self, "planner採用エラー", exc)

    def on_create_task_from_proposal(self) -> None:
        try:
            if self._auto_run_active:
                raise ValueError("auto run active中は proposal から task 作成できません。")
            if self._planner_active:
                raise ValueError("planner generation中は proposal から task 作成できません。")
            if self._plan_director_active:
                raise ValueError("plan_director 実行中は proposal から task 作成できません。")

            repo_path = require_repo_path(self)
            handle_repo_changed(self, repo_path)
            source_task_id = require_selected_task_id(self)
            proposal = self._require_selected_proposal_dict()
            proposal_id = str(proposal["proposal_id"]).strip()
            planner_role = self._get_current_planner_role()

            result = CreateTaskFromProposalUseCase().execute(
                repo_path=repo_path,
                source_task_id=source_task_id,
                proposal_id=proposal_id,
                planner_role=planner_role,
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
                f"planner_role={planner_role}, "
                f"created_task_id={created_task_id}",
            )
            show_info(
                self,
                "task 作成完了",
                "proposal から task を作成しました。\n"
                f"source_task_id: {source_task_id}\n"
                f"proposal_id: {proposal_id}\n"
                f"planner_role: {planner_role}\n"
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
            append_log(
                self,
                "[INFO] planner proposal rejected: "
                f"proposal_id={proposal_id}, "
                f"planner_role={self._get_current_planner_role()}",
            )
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
            append_log(
                self,
                "[INFO] planner proposal deferred: "
                f"proposal_id={proposal_id}, "
                f"planner_role={self._get_current_planner_role()}",
            )
        except Exception as exc:
            show_error(self, "planner保留エラー", exc)

    def on_approve_next_task_from_plan_director(self) -> None:
        try:
            if self._auto_run_active:
                raise ValueError("auto run active中は次task作成を承認できません。")
            if self._planner_active:
                raise ValueError("planner 実行中は次task作成を承認できません。")
            if self._plan_director_active:
                raise ValueError("plan_director 実行中は次task作成を承認できません。")

            if not isinstance(self._plan_director_report, dict):
                raise ValueError("plan_director report がありません。")

            repo_path = require_repo_path(self)
            handle_repo_changed(self, repo_path)
            source_task_id = require_selected_task_id(self)

            self._set_execution_state("running")
            self._set_execution_step("create next task")
            self._set_execution_role("plan_director")
            self._set_execution_cycle(self._get_current_cycle_text())
            self._append_monitor_message("plan_director の採択結果から次taskを作成します")
            append_log(
                self,
                "[INFO] next task creation approved from plan_director",
            )

            result = CreateTaskFromPlanDirectorUseCase().execute(
                repo_path=repo_path,
                source_task_id=source_task_id,
            )

            if not bool(result.get("created")):
                self._set_execution_state("completed")
                self._set_execution_step("no adopt")
                self._set_execution_role("plan_director")
                self._set_execution_cycle(self._get_current_cycle_text())
                self._append_monitor_message(
                    "plan_director の decision が no_adopt のため task は作成されませんでした"
                )
                show_info(
                    self,
                    "task 未作成",
                    "plan_director の decision が no_adopt のため、task は作成されませんでした。",
                )
                return

            created_task_id = str(result["created_task_id"])
            self._current_task_id = created_task_id

            refresh_task_list(self)
            load_selected_task_detail(self, created_task_id)
            self.main_tabs.setCurrentIndex(0)

            append_log(
                self,
                "[INFO] task created from plan_director and auto run will start: "
                f"source_task_id={source_task_id}, "
                f"created_task_id={created_task_id}",
            )

            self._set_execution_state("starting")
            self._set_execution_step("prepare next task auto run")
            self._set_execution_role("task_router")
            self._set_execution_cycle("")
            self._append_monitor_message(
                f"next task created: {created_task_id}. 自動実行を開始します"
            )

            self.on_run_claude_step()
        except Exception as exc:
            show_error(self, "plan_director 承認エラー", exc)

    def on_skip_next_task_from_plan_director(self) -> None:
        try:
            self._set_execution_state("waiting_approval")
            self._set_execution_step("next task skipped")
            self._set_execution_role("plan_director")
            self._set_execution_cycle(self._get_current_cycle_text())
            self._append_monitor_message("次task作成は見送りました")
            append_log(self, "[INFO] 次task作成は見送りました。")
            show_info(
                self,
                "次task見送り",
                "plan_director の結果は保持したまま、今回は次task作成を行いません。",
            )
        except Exception as exc:
            show_error(self, "次task見送りエラー", exc)

    def _start_planner_generation(self, *, auto_run_plan_director: bool) -> None:
        if self._planner_active:
            append_log(self, "[INFO] planner generation is already active.")
            return

        if self._plan_director_active:
            raise ValueError("plan_director 実行中は planner を起動できません。")

        repo_path = require_repo_path(self)
        handle_repo_changed(self, repo_path)
        source_task_id = require_selected_task_id(self)
        planner_role = self._get_current_planner_role()

        self._reset_planner_view()
        self._planner_active = True
        self._pending_auto_plan_director_after_planner = auto_run_plan_director
        self._set_planner_controls_enabled(False)

        self._set_execution_state("running")
        self._set_execution_step("planner")
        self._set_execution_role(planner_role)
        self._set_execution_cycle(self._get_current_cycle_text())
        self._append_monitor_message(f"{planner_role} を開始しました")

        from PySide6.QtCore import QThread

        self._planner_thread = QThread(self)
        self._planner_worker = PlannerWorker(
            repo_path=repo_path,
            source_task_id=source_task_id,
            reference_doc_paths=self._default_reference_doc_paths,
            planner_role=planner_role,
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

    def _start_plan_director_run(self) -> None:
        if self._plan_director_active:
            append_log(self, "[INFO] plan_director is already active.")
            return

        if self._planner_active:
            raise ValueError("planner 実行中は plan_director を起動できません。")

        repo_path = require_repo_path(self)
        handle_repo_changed(self, repo_path)
        source_task_id = require_selected_task_id(self)

        if not self._planner_report:
            raise ValueError("planner report が無いため plan_director を実行できません。")

        self._plan_director_active = True
        self._plan_director_report = None
        self._set_planner_controls_enabled(False)

        self._set_execution_state("running")
        self._set_execution_step("plan_director")
        self._set_execution_role("plan_director")
        self._set_execution_cycle(self._get_current_cycle_text())
        self._append_monitor_message("plan_director を開始しました")

        from PySide6.QtCore import QThread

        self._plan_director_thread = QThread(self)
        self._plan_director_worker = PlanDirectorWorker(
            repo_path=repo_path,
            source_task_id=source_task_id,
        )
        self._plan_director_worker.moveToThread(self._plan_director_thread)

        self._plan_director_thread.started.connect(self._plan_director_worker.run)
        self._plan_director_worker.log_message.connect(self._on_plan_director_log_message)
        self._plan_director_worker.result_ready.connect(
            self._on_plan_director_result_ready
        )
        self._plan_director_worker.error_signal.connect(
            self._on_plan_director_error
        )
        self._plan_director_worker.finished.connect(self._plan_director_thread.quit)
        self._plan_director_worker.finished.connect(
            self._plan_director_worker.deleteLater
        )
        self._plan_director_thread.finished.connect(
            self._on_plan_director_thread_finished
        )
        self._plan_director_thread.finished.connect(
            self._plan_director_thread.deleteLater
        )

        self._plan_director_thread.start()

    def _reset_planner_view(self) -> None:
        clear_planner_area(self)
        self._planner_report = None
        self._planner_state_store = None
        self._planner_selected_proposal_id = ""
        self._plan_director_report = None

        self.plan_director_decision_edit.clear()
        self.plan_director_selected_proposal_edit.clear()
        self.plan_director_reason_edit.clear()
        self.plan_director_scores_edit.clear()

        self._update_planner_action_buttons()

    def _load_existing_planner_data(self, task_id: str) -> None:
        self._reset_planner_view()

        try:
            repo_path = require_repo_path(self)
            planner_role = self._get_current_planner_role()
            runtime = PlannerRuntime(
                target_repo=Path(repo_path).resolve(),
                source_task_id=task_id,
            )
            state_json = runtime.load_source_state_json()
            cycle = int(state_json["cycle"])
            report_path = runtime.get_report_path(
                cycle=cycle,
                planner_role=planner_role,
            )
            if not report_path.exists():
                return

            planner_report = self._json_load_path(report_path)
            self._planner_report = planner_report
            self._planner_state_store = ProposalStateStore(
                repo_path=repo_path,
                source_task_id=task_id,
                cycle=cycle,
            )
            self._planner_state_store.state_path = (
                self._planner_state_store.planner_dir
                / f"{planner_role}_proposal_states_v{cycle}.json"
            )
            self._refresh_planner_list_from_current_report()

            plan_director_path = (
                Path(repo_path)
                / ".claude_orchestrator"
                / "tasks"
                / task_id
                / "planner"
                / f"plan_director_report_v{cycle}.json"
            )
            if plan_director_path.exists():
                self._plan_director_report = self._json_load_path(plan_director_path)
                self._refresh_plan_director_view()
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

    def _refresh_plan_director_view(self) -> None:
        report = self._plan_director_report
        if not isinstance(report, dict):
            self.plan_director_decision_edit.clear()
            self.plan_director_selected_proposal_edit.clear()
            self.plan_director_reason_edit.clear()
            self.plan_director_scores_edit.clear()
            self._update_planner_action_buttons()
            return

        decision = str(report.get("decision", "")).strip()
        selected_proposal_id = report.get("selected_proposal_id")
        selection_reason = str(report.get("selection_reason", "")).strip()
        scores = report.get("scores", []) or []

        self.plan_director_decision_edit.setText(decision)
        self.plan_director_selected_proposal_edit.setText(
            "" if selected_proposal_id is None else str(selected_proposal_id)
        )
        self.plan_director_reason_edit.setPlainText(selection_reason)

        score_lines: list[str] = []
        for item in scores:
            planner_role = str(item.get("planner_role", "")).strip()
            proposal_id = str(item.get("proposal_id", "")).strip()
            proposal_state = str(item.get("proposal_state", "")).strip()
            score = item.get("score")
            reason = str(item.get("reason", "")).strip()
            score_lines.extend(
                [
                    f"[{planner_role}] {proposal_id}",
                    f"state: {proposal_state}",
                    f"score: {score}",
                    reason,
                    "",
                ]
            )
        self.plan_director_scores_edit.setPlainText("\n".join(score_lines).strip())

        if decision == "adopt":
            self._set_execution_state("waiting_approval")
            self._set_execution_step("next task approval")
            self._set_execution_role("plan_director")
            self._set_execution_cycle(self._get_current_cycle_text())
            self._append_monitor_message(
                "plan_director が adopt を返しました。次task作成の承認待ちです"
            )
        elif decision == "no_adopt":
            self._set_execution_state("completed")
            self._set_execution_step("post-planning done")
            self._set_execution_role("plan_director")
            self._set_execution_cycle(self._get_current_cycle_text())
            self._append_monitor_message(
                "plan_director が no_adopt を返しました。今回は次taskを作成しません"
            )

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
        planner_role = str(result.get("planner_role", self._get_current_planner_role()))
        cycle = int(result["cycle"])

        self._planner_report = planner_report
        self._planner_state_store = ProposalStateStore(
            repo_path=repo_path,
            source_task_id=source_task_id,
            cycle=cycle,
        )
        self._planner_state_store.state_path = (
            self._planner_state_store.planner_dir
            / f"{planner_role}_proposal_states_v{cycle}.json"
        )
        self._planner_state_store.initialize_from_report(planner_report)
        self._refresh_planner_list_from_current_report()

        prompt_path = str(result["prompt_path"])
        output_json_path = str(result["output_json_path"])
        self.current_prompt_path_edit.setText(prompt_path)
        self.current_output_json_path_edit.setText(output_json_path)
        self.prompt_text_edit.setPlainText(read_text_file_if_exists(prompt_path))
        self.output_path_detail_edit.setPlainText(output_json_path)

        self._set_execution_state("running")
        self._set_execution_step("planner completed")
        self._set_execution_role(planner_role)
        self._set_execution_cycle(str(cycle))
        self._append_monitor_message(f"{planner_role} が完了しました")

        append_log(
            self,
            "[INFO] planner report saved: "
            f"{output_json_path} "
            f"(planner_role={planner_role})",
        )

    def _on_planner_error(self, title: str, message: str) -> None:
        self._pending_auto_plan_director_after_planner = False
        self._set_execution_state("failed")
        self._set_execution_step("planner failed")
        self._set_execution_role(self._get_current_planner_role())
        self._set_execution_cycle(self._get_current_cycle_text())
        self._append_monitor_message(message)
        append_log(self, f"[ERROR] {message}")
        show_error(self, title, RuntimeError(message))

    def _on_planner_thread_finished(self) -> None:
        self._planner_active = False
        self._planner_worker = None
        self._planner_thread = None
        self._set_planner_controls_enabled(True)

        if self._pending_auto_plan_director_after_planner:
            self._pending_auto_plan_director_after_planner = False
            if self._planner_report:
                try:
                    self._start_plan_director_run()
                except Exception as exc:
                    show_error(self, "自動 plan_director 起動エラー", exc)

        if self._current_task_id:
            self._load_existing_planner_data(self._current_task_id)

    def _on_plan_director_log_message(self, message: str) -> None:
        append_log(self, message)

    def _on_plan_director_result_ready(self, result: object) -> None:
        if not isinstance(result, dict):
            return

        report = result.get("plan_director_report")
        if not isinstance(report, dict):
            raise ValueError("plan_director_report is invalid.")

        self._plan_director_report = report
        self._refresh_plan_director_view()

        prompt_path = str(result["prompt_path"])
        output_json_path = str(result["output_json_path"])
        self.current_prompt_path_edit.setText(prompt_path)
        self.current_output_json_path_edit.setText(output_json_path)
        self.prompt_text_edit.setPlainText(read_text_file_if_exists(prompt_path))
        self.output_path_detail_edit.setPlainText(output_json_path)

        append_log(
            self,
            "[INFO] plan_director report saved: "
            f"{output_json_path}",
        )

    def _on_plan_director_error(self, title: str, message: str) -> None:
        self._set_execution_state("failed")
        self._set_execution_step("plan_director failed")
        self._set_execution_role("plan_director")
        self._set_execution_cycle(self._get_current_cycle_text())
        self._append_monitor_message(message)
        append_log(self, f"[ERROR] {message}")
        show_error(self, title, RuntimeError(message))

    def _on_plan_director_thread_finished(self) -> None:
        self._plan_director_active = False
        self._plan_director_worker = None
        self._plan_director_thread = None
        self._set_planner_controls_enabled(True)
        self._refresh_plan_director_view()

    def _get_current_planner_role(self) -> str:
        combo = getattr(self, "planner_role_combo", None)
        if combo is not None:
            current_data = combo.currentData()
            if isinstance(current_data, str) and current_data in {
                "planner_safe",
                "planner_improvement",
            }:
                return current_data

            current_text = str(combo.currentText()).strip()
            mapping = {
                "planner_safe": "planner_safe",
                "planner_improvement": "planner_improvement",
                "safe": "planner_safe",
                "improvement": "planner_improvement",
            }
            if current_text in mapping:
                return mapping[current_text]

        planner_role = str(getattr(self, "_planner_role", "planner_safe")).strip()
        if planner_role not in {"planner_safe", "planner_improvement"}:
            return "planner_safe"
        return planner_role

    def _get_current_cycle_text(self) -> str:
        for attr_name in ("current_task_cycle_edit", "detail_cycle", "execution_cycle_edit"):
            widget = getattr(self, attr_name, None)
            if widget is None:
                continue
            getter = getattr(widget, "text", None)
            if callable(getter):
                text = str(getter()).strip()
                if text:
                    return text
        return ""

    @staticmethod
    def _json_load_path(path: Path) -> dict:
        with path.open("r", encoding="utf-8") as file:
            return json.load(file)
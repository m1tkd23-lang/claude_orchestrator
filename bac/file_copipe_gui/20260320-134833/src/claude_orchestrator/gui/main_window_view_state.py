# src\claude_orchestrator\gui\main_window_view_state.py
from __future__ import annotations

from claude_orchestrator.gui.state_helpers import read_text_file_if_exists


class MainWindowViewStateMixin:
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

    def _is_pipeline_busy(self) -> bool:
        return bool(
            self._auto_run_active
            or self._planner_active
            or self._plan_director_active
            or self._pending_auto_planner_after_completion
            or self._pending_auto_plan_director_after_planner
            or self._waiting_next_task_approval
        )

    def _refresh_pipeline_controls(self) -> None:
        busy = self._is_pipeline_busy()
        base_enabled = not busy

        self.repo_path_edit.setEnabled(base_enabled)
        self.btn_repo_browse.setEnabled(base_enabled)
        self.btn_check_init.setEnabled(base_enabled)
        self.btn_init_project.setEnabled(base_enabled)

        self.task_title_edit.setEnabled(base_enabled)
        self.task_desc_edit.setEnabled(base_enabled)
        self.context_files_edit.setEnabled(base_enabled)
        self.constraints_edit.setEnabled(base_enabled)
        self.btn_create_task.setEnabled(base_enabled)

        self.task_list_widget.setEnabled(base_enabled)
        self.btn_refresh_tasks.setEnabled(base_enabled)

        self.btn_run_claude_step.setEnabled(base_enabled)

        stop_button_enabled = bool(
            self._auto_run_active
            and not self._planner_active
            and not self._plan_director_active
            and not self._waiting_next_task_approval
        )
        self.btn_request_stop_after_current_task.setEnabled(stop_button_enabled)
        self.btn_request_stop_after_current_task.setText(
            "停止予約済み"
            if self._stop_after_current_task_requested
            else "完了後停止予約"
        )

        self.btn_show_next.setEnabled(base_enabled)
        self.btn_validate.setEnabled(base_enabled)
        self.btn_advance.setEnabled(base_enabled)
        self.btn_reload_selected.setEnabled(base_enabled)

        self.remote_session_name_edit.setEnabled(base_enabled)
        self.remote_spawn_mode_combo.setEnabled(base_enabled)
        self.remote_permission_mode_combo.setEnabled(base_enabled)
        self.btn_connect_remote_claude.setEnabled(base_enabled)
        self.btn_reload_remote_state.setEnabled(base_enabled)
        self.btn_copy_remote_url.setEnabled(base_enabled)

        self.btn_generate_next_tasks.setEnabled(base_enabled)
        self.btn_run_plan_director.setEnabled(base_enabled and bool(self._planner_report))
        self.planner_role_combo.setEnabled(base_enabled)
        self.planner_proposal_list_widget.setEnabled(base_enabled)

        self._update_planner_action_buttons(base_enabled=base_enabled)

    def _set_auto_run_controls_enabled(self, enabled: bool) -> None:
        _ = enabled
        self._refresh_pipeline_controls()

    def _set_planner_controls_enabled(self, enabled: bool) -> None:
        _ = enabled
        self._refresh_pipeline_controls()

    def _update_planner_action_buttons(self, base_enabled: bool = True) -> None:
        has_selection = bool(self._planner_selected_proposal_id)
        proposal_enabled = (
            base_enabled
            and has_selection
            and not self._planner_active
            and not self._auto_run_active
            and not self._plan_director_active
            and not self._waiting_next_task_approval
        )

        self.btn_accept_proposal.setEnabled(proposal_enabled)
        self.btn_create_task_from_proposal.setEnabled(proposal_enabled)
        self.btn_reject_proposal.setEnabled(proposal_enabled)
        self.btn_defer_proposal.setEnabled(proposal_enabled)

        decision = ""
        if isinstance(self._plan_director_report, dict):
            decision = str(self._plan_director_report.get("decision", "")).strip()

        approve_enabled = (
            self._waiting_next_task_approval
            and not self._planner_active
            and not self._auto_run_active
            and not self._plan_director_active
            and decision == "adopt"
        )
        skip_enabled = (
            self._waiting_next_task_approval
            and not self._planner_active
            and not self._auto_run_active
            and not self._plan_director_active
            and isinstance(self._plan_director_report, dict)
        )

        self.btn_approve_next_task.setEnabled(approve_enabled)
        self.btn_skip_next_task.setEnabled(skip_enabled)
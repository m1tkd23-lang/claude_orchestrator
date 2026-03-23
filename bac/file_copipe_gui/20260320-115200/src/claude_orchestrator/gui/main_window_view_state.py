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

        self.remote_session_name_edit.setEnabled(enabled)
        self.remote_spawn_mode_combo.setEnabled(enabled)
        self.remote_permission_mode_combo.setEnabled(enabled)
        self.btn_connect_remote_claude.setEnabled(enabled)
        self.btn_reload_remote_state.setEnabled(enabled)
        self.btn_copy_remote_url.setEnabled(enabled)

    def _set_planner_controls_enabled(self, enabled: bool) -> None:
        self.btn_generate_next_tasks.setEnabled(enabled and not self._auto_run_active)
        self.planner_proposal_list_widget.setEnabled(enabled)
        self._update_planner_action_buttons(base_enabled=enabled)

    def _update_planner_action_buttons(self, base_enabled: bool = True) -> None:
        has_selection = bool(self._planner_selected_proposal_id)
        enabled = (
            base_enabled
            and has_selection
            and not self._planner_active
            and not self._auto_run_active
        )

        self.btn_accept_proposal.setEnabled(enabled)
        self.btn_create_task_from_proposal.setEnabled(enabled)
        self.btn_reject_proposal.setEnabled(enabled)
        self.btn_defer_proposal.setEnabled(enabled)
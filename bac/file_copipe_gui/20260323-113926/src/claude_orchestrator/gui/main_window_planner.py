# src\claude_orchestrator\gui\main_window_planner.py
# 置換: _on_plan_director_result_ready
def _on_plan_director_result_ready(self, result: object) -> None:
    if not isinstance(result, dict):
        return

    report = result.get("plan_director_report")
    if not isinstance(report, dict):
        raise ValueError("plan_director_report is invalid.")

    repo_path = require_repo_path(self)
    source_task_id = require_selected_task_id(self)
    cycle = int(result.get("cycle", 0))

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

    decision = str(report.get("decision", "")).strip()
    selected_proposal_id = str(report.get("selected_proposal_id", "") or "").strip()
    selection_reason = str(report.get("selection_reason", "") or "").strip()
    selected_planner_role = str(
        report.get("selected_planner_role", "") or self._get_current_planner_role()
    ).strip()

    selected_state = ""
    if selected_proposal_id and self._planner_state_store is not None:
        selected_state = self._planner_state_store.get_state_map().get(
            selected_proposal_id,
            "",
        )

    approval_store = NextTaskApprovalStore(
        repo_path=repo_path,
        source_task_id=source_task_id,
    )

    if decision == "adopt" and selected_state != "task_created":
        PrepareNextTaskApprovalUseCase().execute(
            repo_path=repo_path,
            source_task_id=source_task_id,
            cycle=cycle,
            decision=decision,
            selected_proposal_id=selected_proposal_id,
            selected_planner_role=selected_planner_role,
            selection_reason=selection_reason,
            executor_type="gui",
            executor_id="gui-main-window",
            executor_label="GUI",
        )
        self._waiting_next_task_approval = True
        self._set_execution_state("waiting_approval")
        self._set_execution_step("next task approval")
        self._set_execution_role("plan_director")
        self._set_execution_cycle(self._get_current_cycle_text())
        self._append_monitor_message(
            "plan_director が adopt を返しました。次task作成の承認待ちです"
        )
    elif decision == "adopt" and selected_state == "task_created":
        approval_store.clear()
        self._waiting_next_task_approval = False
        self._set_execution_state("completed")
        self._set_execution_step("next task already created")
        self._set_execution_role("plan_director")
        self._set_execution_cycle(self._get_current_cycle_text())
        self._append_monitor_message(
            "plan_director の採択proposalは既に task_created 済みです"
        )
    elif decision == "no_adopt":
        approval_store.clear()
        self._waiting_next_task_approval = False
        self._set_execution_state("completed")
        self._set_execution_step("post-planning done")
        self._set_execution_role("plan_director")
        self._set_execution_cycle(self._get_current_cycle_text())
        self._append_monitor_message(
            "plan_director が no_adopt を返しました。今回は次taskを作成しません"
        )
    else:
        approval_store.clear()
        self._waiting_next_task_approval = False

    self._refresh_pipeline_controls()
    self._refresh_pipeline_tab()
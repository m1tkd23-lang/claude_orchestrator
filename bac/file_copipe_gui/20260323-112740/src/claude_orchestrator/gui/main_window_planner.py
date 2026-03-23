# src\claude_orchestrator\gui\main_window_planner.py
# 置換: on_skip_next_task_from_plan_director
def on_skip_next_task_from_plan_director(self) -> None:
    try:
        repo_path = require_repo_path(self)
        handle_repo_changed(self, repo_path)
        source_task_id = require_selected_task_id(self)

        result = RejectNextTaskUseCase().execute(
            repo_path=repo_path,
            source_task_id=source_task_id,
            executor_type="gui",
            executor_id="gui-main-window",
            executor_label="GUI",
        )

        self._waiting_next_task_approval = False
        self._pending_auto_approve_next_task = False
        self._refresh_pipeline_controls()
        self._set_execution_state("stopped")
        self._set_execution_step("next task skipped")
        self._set_execution_role("plan_director")
        self._set_execution_cycle(self._get_current_cycle_text())
        self._append_monitor_message(str(result.get("message", "")).strip() or "次task作成は見送りました")
        append_log(self, "[INFO] 次task作成は見送りました。")
        self._refresh_pipeline_tab()
        show_info(
            self,
            "次task見送り",
            "plan_director の結果は保持したまま、今回は次task作成を行いません。",
        )
    except Exception as exc:
        show_error(self, "次task見送りエラー", exc)
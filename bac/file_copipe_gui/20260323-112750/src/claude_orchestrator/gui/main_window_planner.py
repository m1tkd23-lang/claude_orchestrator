# src\claude_orchestrator\gui\main_window_planner.py
# 置換: _create_next_task_from_plan_director_and_start
def _create_next_task_from_plan_director_and_start(self) -> None:
    repo_path = require_repo_path(self)
    handle_repo_changed(self, repo_path)
    source_task_id = require_selected_task_id(self)

    self._waiting_next_task_approval = False
    self._pending_auto_approve_next_task = False
    self._refresh_pipeline_controls()

    self._set_execution_state("running")
    self._set_execution_step("create next task")
    self._set_execution_role("plan_director")
    self._set_execution_cycle(self._get_current_cycle_text())
    self._append_monitor_message("plan_director の採択結果から次taskを作成します")
    append_log(
        self,
        "[INFO] next task creation approved from plan_director",
    )
    self._refresh_pipeline_tab()

    result = ApproveNextTaskUseCase().execute(
        repo_path=repo_path,
        source_task_id=source_task_id,
        executor_type="gui",
        executor_id="gui-main-window",
        executor_label="GUI",
    )

    if not bool(result.get("approved")):
        message = str(result.get("message", "")).strip()
        self._set_execution_state("completed")
        self._set_execution_step("next task not created")
        self._set_execution_role("plan_director")
        self._set_execution_cycle(self._get_current_cycle_text())
        if message:
            self._append_monitor_message(message)
        self._refresh_pipeline_controls()
        self._refresh_pipeline_tab()
        show_info(
            self,
            "task 未作成",
            message or "次taskは作成されませんでした。",
        )
        return

    created_task_id = str(result.get("created_task_id", "")).strip()
    created_proposal_id = str(result.get("selected_proposal_id", "")).strip()
    created_planner_role = str(result.get("selected_planner_role", "")).strip()

    self._current_task_id = created_task_id

    if (
        created_proposal_id
        and created_planner_role in {"planner_safe", "planner_improvement"}
        and self._planner_state_store is not None
        and created_planner_role == self._get_current_planner_role()
    ):
        self._planner_state_store.set_state(created_proposal_id, "task_created")

    refresh_task_list(self)
    load_selected_task_detail(self, created_task_id)

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

    self._refresh_pipeline_tab()
    self.on_run_claude_step()
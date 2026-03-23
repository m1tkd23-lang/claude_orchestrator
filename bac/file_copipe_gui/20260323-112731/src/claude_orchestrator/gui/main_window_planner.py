# src\claude_orchestrator\gui\main_window_planner.py
# 置換: on_approve_next_task_from_plan_director
def on_approve_next_task_from_plan_director(self) -> None:
    try:
        if self._auto_run_active or self._planner_active or self._plan_director_active:
            raise ValueError("後工程実行中は次task作成を承認できません。")

        if not self._waiting_next_task_approval:
            raise ValueError("現在は次task承認待ち状態ではありません。")

        if not isinstance(self._plan_director_report, dict):
            raise ValueError("plan_director report がありません。")

        self._create_next_task_from_plan_director_and_start()
    except Exception as exc:
        show_error(self, "plan_director 承認エラー", exc)
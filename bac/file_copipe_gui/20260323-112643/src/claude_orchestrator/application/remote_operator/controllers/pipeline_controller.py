# src\claude_orchestrator\application\remote_operator\controllers\pipeline_controller.py
from __future__ import annotations

from claude_orchestrator.application.remote_operator.constants import (
    DEFAULT_PLANNER_ROLE,
    MENU_MAIN,
    MENU_NEXT_TASK_APPROVAL,
    MENU_PIPELINE_SETTINGS,
    MENU_PLAN_DIRECTOR_RESULT,
    MENU_POST_PIPELINE,
    MENU_TASK_LIST,
    PLANNER_IMPROVEMENT,
    PLANNER_SAFE,
)
from claude_orchestrator.infrastructure.remote_session_store import RemoteSessionStore

from claude_orchestrator.application.remote_operator.controller_support import (
    RemoteOperatorControllerSupport,
)


class PipelineController:
    def __init__(self, support: RemoteOperatorControllerSupport) -> None:
        self.support = support

    def handle_post_pipeline(self, *, repo_path: str, choice: str) -> dict:
        store = RemoteSessionStore(repo_path=repo_path)
        payload = store.load()
        source_task_id = self.support.get_post_pipeline_source_task_id(repo_path=repo_path)
        previous_menu = str(payload.get("previous_menu", MENU_MAIN)).strip() or MENU_MAIN
        planner_role = self.support.get_active_planner_role(repo_path=repo_path)

        if not source_task_id:
            return self.support.switch_menu(
                repo_path=repo_path,
                menu=MENU_MAIN,
                last_message="source task が見つからないため、メインメニューへ戻しました。",
                previous_menu=MENU_POST_PIPELINE,
            )

        if choice == "1":
            return self.support.generate_proposals_and_render(
                repo_path=repo_path,
                source_task_id=source_task_id,
                previous_menu=MENU_POST_PIPELINE,
                planner_role=planner_role,
            )

        if choice == "2":
            return self.support.run_plan_director_and_render(
                repo_path=repo_path,
                source_task_id=source_task_id,
                previous_menu=MENU_POST_PIPELINE,
            )

        if choice == "3":
            return self.support.run_post_pipeline_auto_and_render(
                repo_path=repo_path,
                source_task_id=source_task_id,
                previous_menu=MENU_POST_PIPELINE,
            )

        if choice == "4":
            if not bool(payload.get("waiting_next_task_approval", False)):
                return self.support.stay_with_message(
                    repo_path=repo_path,
                    menu=MENU_POST_PIPELINE,
                    last_message="現在、承認待ち案件はありません。",
                )
            return self.support.switch_menu(
                repo_path=repo_path,
                menu=MENU_NEXT_TASK_APPROVAL,
                last_message="承認待ち画面へ移動しました。",
                previous_menu=MENU_POST_PIPELINE,
            )

        if choice == "5":
            return self.support.switch_menu(
                repo_path=repo_path,
                menu=MENU_PIPELINE_SETTINGS,
                last_message="pipeline 設定へ移動しました。",
                previous_menu=MENU_POST_PIPELINE,
            )

        if choice == "6":
            return self.support.switch_menu(
                repo_path=repo_path,
                menu=MENU_TASK_LIST,
                last_message="task 一覧へ移動しました。",
                previous_menu=MENU_POST_PIPELINE,
            )

        if choice == "7":
            return self.support.switch_menu(
                repo_path=repo_path,
                menu=MENU_MAIN,
                last_message="メインメニューへ戻りました。",
                previous_menu=MENU_POST_PIPELINE,
            )

        if choice == "0":
            return self.support.switch_menu(
                repo_path=repo_path,
                menu=previous_menu,
                last_message="前の画面へ戻りました。",
                previous_menu=MENU_POST_PIPELINE,
            )

        return self.support.stay_with_message(
            repo_path=repo_path,
            menu=MENU_POST_PIPELINE,
            last_message="無効な番号です。もう一度選択してください。",
        )

    def handle_plan_director_result(self, *, repo_path: str, choice: str) -> dict:
        decision = self.support.get_last_plan_director_decision(repo_path=repo_path)

        if decision == "adopt":
            if choice == "1":
                return self.support.switch_menu(
                    repo_path=repo_path,
                    menu=MENU_NEXT_TASK_APPROVAL,
                    last_message="承認待ち画面へ移動しました。",
                    previous_menu=MENU_PLAN_DIRECTOR_RESULT,
                )
            if choice == "2":
                return self.support.switch_menu(
                    repo_path=repo_path,
                    menu=MENU_POST_PIPELINE,
                    last_message="後工程メニューへ戻りました。",
                    previous_menu=MENU_PLAN_DIRECTOR_RESULT,
                )
            if choice == "3":
                return self.support.switch_menu(
                    repo_path=repo_path,
                    menu=MENU_TASK_LIST,
                    last_message="task 一覧へ移動しました。",
                    previous_menu=MENU_PLAN_DIRECTOR_RESULT,
                )
            if choice == "0":
                return self.support.switch_menu(
                    repo_path=repo_path,
                    menu=MENU_POST_PIPELINE,
                    last_message="後工程メニューへ戻りました。",
                    previous_menu=MENU_PLAN_DIRECTOR_RESULT,
                )
            return self.support.stay_with_message(
                repo_path=repo_path,
                menu=MENU_PLAN_DIRECTOR_RESULT,
                last_message="無効な番号です。もう一度選択してください。",
            )

        if choice == "1":
            return self.support.switch_menu(
                repo_path=repo_path,
                menu=MENU_POST_PIPELINE,
                last_message="後工程メニューへ戻りました。",
                previous_menu=MENU_PLAN_DIRECTOR_RESULT,
            )
        if choice == "2":
            return self.support.switch_menu(
                repo_path=repo_path,
                menu=MENU_TASK_LIST,
                last_message="task 一覧へ移動しました。",
                previous_menu=MENU_PLAN_DIRECTOR_RESULT,
            )
        if choice == "0":
            return self.support.switch_menu(
                repo_path=repo_path,
                menu=MENU_POST_PIPELINE,
                last_message="後工程メニューへ戻りました。",
                previous_menu=MENU_PLAN_DIRECTOR_RESULT,
            )

        return self.support.stay_with_message(
            repo_path=repo_path,
            menu=MENU_PLAN_DIRECTOR_RESULT,
            last_message="無効な番号です。もう一度選択してください。",
        )

    def handle_next_task_approval(self, *, repo_path: str, choice: str) -> dict:
        source_task_id = self.support.get_post_pipeline_source_task_id(repo_path=repo_path)

        if not source_task_id:
            return self.support.switch_menu(
                repo_path=repo_path,
                menu=MENU_POST_PIPELINE,
                last_message="承認対象の source task が見つかりません。",
                previous_menu=MENU_NEXT_TASK_APPROVAL,
            )

        if choice == "1":
            return self.support.create_task_from_plan_director_and_render(
                repo_path=repo_path,
                source_task_id=source_task_id,
                previous_menu=MENU_NEXT_TASK_APPROVAL,
                message_prefix="次 task 作成を承認しました。",
            )

        if choice == "2":
            store = RemoteSessionStore(repo_path=repo_path)
            store.update_fields(
                waiting_next_task_approval=False,
                current_menu=MENU_POST_PIPELINE,
                previous_menu=MENU_NEXT_TASK_APPROVAL,
                last_message="今回は次 task を作成しません。",
            )
            return self.support.render_result(
                repo_path=repo_path,
                menu=MENU_POST_PIPELINE,
                last_message="今回は次 task を作成しません。",
            )

        if choice == "3" or choice == "0":
            return self.support.switch_menu(
                repo_path=repo_path,
                menu=MENU_POST_PIPELINE,
                last_message="後工程メニューへ戻りました。",
                previous_menu=MENU_NEXT_TASK_APPROVAL,
            )

        return self.support.stay_with_message(
            repo_path=repo_path,
            menu=MENU_NEXT_TASK_APPROVAL,
            last_message="無効な番号です。もう一度選択してください。",
        )

    def handle_pipeline_settings(self, *, repo_path: str, choice: str) -> dict:
        store = RemoteSessionStore(repo_path=repo_path)
        payload = store.load()
        previous_menu = str(payload.get("previous_menu", MENU_POST_PIPELINE)).strip() or MENU_POST_PIPELINE

        if choice == "1":
            store.update_fields(
                active_planner_role=PLANNER_SAFE,
                last_message="active_planner_role を planner_safe に変更しました。",
            )
            return self.support.render_result(
                repo_path=repo_path,
                menu=MENU_PIPELINE_SETTINGS,
                last_message="active_planner_role を planner_safe に変更しました。",
            )

        if choice == "2":
            store.update_fields(
                active_planner_role=PLANNER_IMPROVEMENT,
                last_message="active_planner_role を planner_improvement に変更しました。",
            )
            return self.support.render_result(
                repo_path=repo_path,
                menu=MENU_PIPELINE_SETTINGS,
                last_message="active_planner_role を planner_improvement に変更しました。",
            )

        if choice == "3":
            store.update_fields(
                approval_mode="manual",
                last_message="approval_mode を manual に変更しました。",
            )
            return self.support.render_result(
                repo_path=repo_path,
                menu=MENU_PIPELINE_SETTINGS,
                last_message="approval_mode を manual に変更しました。",
            )

        if choice == "4":
            store.update_fields(
                approval_mode="auto",
                last_message="approval_mode を auto に変更しました。",
            )
            return self.support.render_result(
                repo_path=repo_path,
                menu=MENU_PIPELINE_SETTINGS,
                last_message="approval_mode を auto に変更しました。",
            )

        if choice == "5":
            current = bool(payload.get("stop_after_current_task_requested", False))
            store.update_fields(
                stop_after_current_task_requested=not current,
                last_message=(
                    "stop_reservation を ON にしました。"
                    if not current
                    else "stop_reservation を OFF にしました。"
                ),
            )
            return self.support.render_result(
                repo_path=repo_path,
                menu=MENU_PIPELINE_SETTINGS,
                last_message=(
                    "stop_reservation を ON にしました。"
                    if not current
                    else "stop_reservation を OFF にしました。"
                ),
            )

        if choice == "6":
            self.support.set_development_mode(
                repo_path=repo_path,
                development_mode="maintenance",
            )
            return self.support.render_result(
                repo_path=repo_path,
                menu=MENU_PIPELINE_SETTINGS,
                last_message="development_mode を maintenance に変更しました。",
            )

        if choice == "7":
            self.support.set_development_mode(
                repo_path=repo_path,
                development_mode="mainline",
            )
            return self.support.render_result(
                repo_path=repo_path,
                menu=MENU_PIPELINE_SETTINGS,
                last_message="development_mode を mainline に変更しました。",
            )

        if choice == "0":
            return self.support.switch_menu(
                repo_path=repo_path,
                menu=previous_menu,
                last_message="前の画面へ戻りました。",
                previous_menu=MENU_PIPELINE_SETTINGS,
            )

        return self.support.stay_with_message(
            repo_path=repo_path,
            menu=MENU_PIPELINE_SETTINGS,
            last_message="無効な番号です。もう一度選択してください。",
        )
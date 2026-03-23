# src\claude_orchestrator\application\remote_operator\controller.py
from __future__ import annotations

from claude_orchestrator.application.remote_operator.constants import (
    DEFAULT_MENU,
    MENU_COMPLETED_TASK_LIST,
    MENU_CREATED_TASK,
    MENU_EXITED,
    MENU_IN_PROGRESS_TASK_LIST,
    MENU_MAIN,
    MENU_NEXT_TASK_APPROVAL,
    MENU_PIPELINE_SETTINGS,
    MENU_PLAN_DIRECTOR_RESULT,
    MENU_POST_PIPELINE,
    MENU_POST_RUN,
    MENU_PROPOSAL_LIST,
    MENU_SELECTED_PROPOSAL,
    MENU_SELECTED_TASK,
    MENU_TASK_LIST,
)
from claude_orchestrator.application.remote_operator.controller_support import (
    RemoteOperatorControllerSupport,
)
from claude_orchestrator.application.remote_operator.controllers.main_menu_controller import (
    MainMenuController,
)
from claude_orchestrator.application.remote_operator.controllers.pipeline_controller import (
    PipelineController,
)
from claude_orchestrator.application.remote_operator.controllers.proposal_controller import (
    ProposalController,
)
from claude_orchestrator.application.remote_operator.controllers.selected_task_controller import (
    SelectedTaskController,
)
from claude_orchestrator.application.remote_operator.controllers.task_list_controller import (
    TaskListController,
)
from claude_orchestrator.infrastructure.remote_session_store import RemoteSessionStore


class RemoteOperatorController:
    def __init__(self) -> None:
        self.support = RemoteOperatorControllerSupport()
        self.main_menu_controller = MainMenuController(self.support)
        self.task_list_controller = TaskListController(self.support)
        self.selected_task_controller = SelectedTaskController(self.support)
        self.proposal_controller = ProposalController(self.support)
        self.pipeline_controller = PipelineController(self.support)

    def show_menu(self, *, repo_path: str) -> dict:
        store = RemoteSessionStore(repo_path=repo_path)
        payload = store.load()
        current_menu = str(payload.get("current_menu", DEFAULT_MENU)).strip() or DEFAULT_MENU
        last_message = str(payload.get("last_message", "")).strip()

        text = self.support.render_current_menu(
            repo_path=repo_path,
            current_menu=current_menu,
            last_message=last_message,
        )
        return {
            "menu": current_menu,
            "text": text,
        }

    def handle_input(
        self,
        *,
        repo_path: str,
        user_input: str,
    ) -> dict:
        normalized = str(user_input).strip()

        store = RemoteSessionStore(repo_path=repo_path)
        payload = store.load()
        current_menu = str(payload.get("current_menu", DEFAULT_MENU)).strip() or DEFAULT_MENU

        if not normalized.isdigit():
            return self.support.stay_with_message(
                repo_path=repo_path,
                menu=current_menu,
                last_message="無効な入力です。番号で入力してください。",
            )

        if current_menu == MENU_MAIN:
            return self.main_menu_controller.handle(repo_path=repo_path, choice=normalized)

        if current_menu == MENU_IN_PROGRESS_TASK_LIST:
            return self.task_list_controller.handle_in_progress(
                repo_path=repo_path,
                choice=normalized,
            )

        if current_menu == MENU_COMPLETED_TASK_LIST:
            return self.task_list_controller.handle_completed(
                repo_path=repo_path,
                choice=normalized,
            )

        if current_menu == MENU_TASK_LIST:
            return self.task_list_controller.handle_all(
                repo_path=repo_path,
                choice=normalized,
            )

        if current_menu == MENU_SELECTED_TASK:
            return self.selected_task_controller.handle(
                repo_path=repo_path,
                choice=normalized,
            )

        if current_menu == MENU_PROPOSAL_LIST:
            return self.proposal_controller.handle_list(
                repo_path=repo_path,
                choice=normalized,
            )

        if current_menu == MENU_SELECTED_PROPOSAL:
            return self.proposal_controller.handle_selected(
                repo_path=repo_path,
                choice=normalized,
            )

        if current_menu == MENU_CREATED_TASK:
            return self.selected_task_controller.handle_created_task(
                repo_path=repo_path,
                choice=normalized,
            )

        if current_menu == MENU_POST_RUN:
            return self.selected_task_controller.handle_post_run(
                repo_path=repo_path,
                choice=normalized,
            )

        if current_menu == MENU_POST_PIPELINE:
            return self.pipeline_controller.handle_post_pipeline(
                repo_path=repo_path,
                choice=normalized,
            )

        if current_menu == MENU_PLAN_DIRECTOR_RESULT:
            return self.pipeline_controller.handle_plan_director_result(
                repo_path=repo_path,
                choice=normalized,
            )

        if current_menu == MENU_NEXT_TASK_APPROVAL:
            return self.pipeline_controller.handle_next_task_approval(
                repo_path=repo_path,
                choice=normalized,
            )

        if current_menu == MENU_PIPELINE_SETTINGS:
            return self.pipeline_controller.handle_pipeline_settings(
                repo_path=repo_path,
                choice=normalized,
            )

        if current_menu == MENU_EXITED:
            if normalized == "0":
                return self.support.switch_menu(
                    repo_path=repo_path,
                    menu=MENU_MAIN,
                    last_message="メインメニューへ戻りました。",
                    previous_menu=MENU_EXITED,
                )
            return self.support.stay_with_message(
                repo_path=repo_path,
                menu=MENU_EXITED,
                last_message="終了状態です。0 を入力するとメインメニューへ戻ります。",
            )

        store.reset_operator_state()
        return self.support.render_result(
            repo_path=repo_path,
            menu=MENU_MAIN,
            last_message="メニュー状態が不正だったため、メインメニューへ戻しました。",
        )
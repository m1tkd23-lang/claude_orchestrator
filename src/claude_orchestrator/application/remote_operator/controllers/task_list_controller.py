# src\claude_orchestrator\application\remote_operator\controllers\task_list_controller.py
from __future__ import annotations

from claude_orchestrator.application.remote_operator.constants import (
    MENU_COMPLETED_TASK_LIST,
    MENU_IN_PROGRESS_TASK_LIST,
    MENU_MAIN,
    MENU_TASK_LIST,
    MENU_SELECTED_TASK,
)
from claude_orchestrator.application.usecases.status_usecase import StatusUseCase
from claude_orchestrator.infrastructure.remote_session_store import RemoteSessionStore

from claude_orchestrator.application.remote_operator.controller_support import (
    RemoteOperatorControllerSupport,
)


class TaskListController:
    def __init__(self, support: RemoteOperatorControllerSupport) -> None:
        self.support = support

    def handle_in_progress(self, *, repo_path: str, choice: str) -> dict:
        if choice == "0":
            return self.support.switch_menu(
                repo_path=repo_path,
                menu=MENU_MAIN,
                last_message="メインメニューへ戻りました。",
                previous_menu=MENU_IN_PROGRESS_TASK_LIST,
            )

        tasks = self.support.list_in_progress_tasks(repo_path=repo_path)
        selected = self.support.select_from_numbered_items(tasks, choice)
        if selected is None:
            return self.support.stay_with_message(
                repo_path=repo_path,
                menu=MENU_IN_PROGRESS_TASK_LIST,
                last_message="無効な番号です。もう一度選択してください。",
            )

        return self.support.run_task_and_render(
            repo_path=repo_path,
            task_id=str(selected["task_id"]),
            previous_menu=MENU_IN_PROGRESS_TASK_LIST,
        )

    def handle_completed(self, *, repo_path: str, choice: str) -> dict:
        if choice == "0":
            return self.support.switch_menu(
                repo_path=repo_path,
                menu=MENU_MAIN,
                last_message="メインメニューへ戻りました。",
                previous_menu=MENU_COMPLETED_TASK_LIST,
            )

        tasks = self.support.list_completed_tasks(repo_path=repo_path)
        selected = self.support.select_from_numbered_items(tasks, choice)
        if selected is None:
            return self.support.stay_with_message(
                repo_path=repo_path,
                menu=MENU_COMPLETED_TASK_LIST,
                last_message="無効な番号です。もう一度選択してください。",
            )

        return self.support.enter_post_pipeline(
            repo_path=repo_path,
            source_task_id=str(selected["task_id"]),
            previous_menu=MENU_COMPLETED_TASK_LIST,
            last_message=f"{selected['task_id']} の後工程メニューへ移動しました。",
        )

    def handle_all(self, *, repo_path: str, choice: str) -> dict:
        if choice == "0":
            return self.support.switch_menu(
                repo_path=repo_path,
                menu=MENU_MAIN,
                last_message="メインメニューへ戻りました。",
                previous_menu=MENU_TASK_LIST,
            )

        tasks = StatusUseCase().list_tasks(repo_path=repo_path)
        selected = self.support.select_from_numbered_items(tasks, choice)
        if selected is None:
            return self.support.stay_with_message(
                repo_path=repo_path,
                menu=MENU_TASK_LIST,
                last_message="無効な番号です。もう一度選択してください。",
            )

        task_id = str(selected["task_id"]).strip()
        store = RemoteSessionStore(repo_path=repo_path)
        store.update_fields(
            selected_task_id=task_id,
            selected_source_task_id="",
            selected_proposal_id="",
            selected_proposal_planner_role="",
            current_menu=MENU_SELECTED_TASK,
            previous_menu=MENU_TASK_LIST,
            last_message=f"{task_id} を選択しました。",
        )
        return self.support.render_result(
            repo_path=repo_path,
            menu=MENU_SELECTED_TASK,
            last_message=f"{task_id} を選択しました。",
        )
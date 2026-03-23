# src\claude_orchestrator\application\remote_operator\controllers\main_menu_controller.py
from __future__ import annotations

from claude_orchestrator.application.remote_operator.constants import (
    MENU_COMPLETED_TASK_LIST,
    MENU_EXITED,
    MENU_IN_PROGRESS_TASK_LIST,
    MENU_MAIN,
    MENU_TASK_LIST,
)
from claude_orchestrator.infrastructure.remote_session_store import RemoteSessionStore

from claude_orchestrator.application.remote_operator.controller_support import (
    RemoteOperatorControllerSupport,
)


class MainMenuController:
    def __init__(self, support: RemoteOperatorControllerSupport) -> None:
        self.support = support

    def handle(self, *, repo_path: str, choice: str) -> dict:
        if choice == "1":
            tasks = self.support.list_in_progress_tasks(repo_path=repo_path)
            if not tasks:
                return self.support.stay_with_message(
                    repo_path=repo_path,
                    menu=MENU_MAIN,
                    last_message="in_progress task はありません。",
                )
            if len(tasks) == 1:
                task_id = str(tasks[0]["task_id"])
                return self.support.run_task_and_render(
                    repo_path=repo_path,
                    task_id=task_id,
                    previous_menu=MENU_MAIN,
                )
            return self.support.switch_menu(
                repo_path=repo_path,
                menu=MENU_IN_PROGRESS_TASK_LIST,
                last_message="実行する in_progress task を選択してください。",
                previous_menu=MENU_MAIN,
            )

        if choice == "2":
            tasks = self.support.list_completed_tasks(repo_path=repo_path)
            if not tasks:
                return self.support.stay_with_message(
                    repo_path=repo_path,
                    menu=MENU_MAIN,
                    last_message="completed task はありません。",
                )
            if len(tasks) == 1:
                task_id = str(tasks[0]["task_id"])
                return self.support.enter_post_pipeline(
                    repo_path=repo_path,
                    source_task_id=task_id,
                    previous_menu=MENU_MAIN,
                    last_message=f"{task_id} の後工程メニューへ移動しました。",
                )
            return self.support.switch_menu(
                repo_path=repo_path,
                menu=MENU_COMPLETED_TASK_LIST,
                last_message="後工程を操作する completed task を選択してください。",
                previous_menu=MENU_MAIN,
            )

        if choice in {"3", "4"}:
            return self.support.switch_menu(
                repo_path=repo_path,
                menu=MENU_TASK_LIST,
                last_message="task 一覧です。番号で task を選択してください。",
                previous_menu=MENU_MAIN,
            )

        if choice == "5":
            store = RemoteSessionStore(repo_path=repo_path)
            store.update_fields(
                current_menu=MENU_EXITED,
                previous_menu=MENU_MAIN,
                last_message="Remote Operator を終了状態にしました。",
            )
            return self.support.render_result(
                repo_path=repo_path,
                menu=MENU_EXITED,
                last_message="Remote Operator を終了状態にしました。",
            )

        return self.support.stay_with_message(
            repo_path=repo_path,
            menu=MENU_MAIN,
            last_message="無効な入力です。番号で入力してください。",
        )
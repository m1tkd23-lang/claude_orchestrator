# src\claude_orchestrator\application\remote_operator\controllers\selected_task_controller.py
from __future__ import annotations

from claude_orchestrator.application.remote_operator.constants import (
    MENU_CREATED_TASK,
    MENU_MAIN,
    MENU_POST_RUN,
    MENU_SELECTED_TASK,
    MENU_TASK_LIST,
)
from claude_orchestrator.application.usecases.status_usecase import StatusUseCase
from claude_orchestrator.infrastructure.remote_session_store import RemoteSessionStore

from claude_orchestrator.application.remote_operator.controller_support import (
    RemoteOperatorControllerSupport,
)


class SelectedTaskController:
    def __init__(self, support: RemoteOperatorControllerSupport) -> None:
        self.support = support

    def handle(self, *, repo_path: str, choice: str) -> dict:
        store = RemoteSessionStore(repo_path=repo_path)
        payload = store.load()
        task_id = str(payload.get("selected_task_id", "")).strip()

        if not task_id:
            return self.support.switch_menu(
                repo_path=repo_path,
                menu=MENU_TASK_LIST,
                last_message="選択中 task が無いため、task 一覧へ戻しました。",
                previous_menu=MENU_SELECTED_TASK,
            )

        task = StatusUseCase().get_task_status(repo_path=repo_path, task_id=task_id)
        status = str(task.get("status", "")).strip()

        if choice == "1":
            return self.support.stay_with_message(
                repo_path=repo_path,
                menu=MENU_SELECTED_TASK,
                last_message=f"{task_id} の詳細を再表示します。",
            )

        if choice == "2":
            if status == "in_progress":
                return self.support.run_task_and_render(
                    repo_path=repo_path,
                    task_id=task_id,
                    previous_menu=MENU_SELECTED_TASK,
                )
            if status == "completed":
                return self.support.enter_post_pipeline(
                    repo_path=repo_path,
                    source_task_id=task_id,
                    previous_menu=MENU_SELECTED_TASK,
                    last_message=f"{task_id} の後工程メニューへ移動しました。",
                )
            return self.support.stay_with_message(
                repo_path=repo_path,
                menu=MENU_SELECTED_TASK,
                last_message=(
                    f"{task_id} は status={status} のため、"
                    "この操作は実行できません。"
                ),
            )

        if choice == "3":
            if status == "in_progress":
                return self.support.run_standard_task_pipeline_and_render(
                    repo_path=repo_path,
                    task_id=task_id,
                    previous_menu=MENU_SELECTED_TASK,
                )
            if status == "completed":
                return self.support.run_post_pipeline_auto_and_render(
                    repo_path=repo_path,
                    source_task_id=task_id,
                    previous_menu=MENU_SELECTED_TASK,
                )
            return self.support.stay_with_message(
                repo_path=repo_path,
                menu=MENU_SELECTED_TASK,
                last_message=(
                    f"{task_id} は status={status} のため、"
                    "この操作は実行できません。"
                ),
            )

        if choice == "0":
            return self.support.switch_menu(
                repo_path=repo_path,
                menu=MENU_TASK_LIST,
                last_message="task 一覧へ戻りました。",
                previous_menu=MENU_SELECTED_TASK,
            )

        return self.support.stay_with_message(
            repo_path=repo_path,
            menu=MENU_SELECTED_TASK,
            last_message="無効な番号です。もう一度選択してください。",
        )

    def handle_created_task(self, *, repo_path: str, choice: str) -> dict:
        store = RemoteSessionStore(repo_path=repo_path)
        payload = store.load()
        task_id = str(payload.get("selected_task_id", "")).strip()
        source_task_id = str(payload.get("selected_source_task_id", "")).strip()
        previous_menu = str(payload.get("previous_menu", MENU_MAIN)).strip() or MENU_MAIN

        if not task_id:
            return self.support.switch_menu(
                repo_path=repo_path,
                menu=MENU_MAIN,
                last_message="作成済み task が見つからないため、メインメニューへ戻しました。",
                previous_menu=MENU_CREATED_TASK,
            )

        if choice == "1":
            return self.support.run_standard_task_pipeline_and_render(
                repo_path=repo_path,
                task_id=task_id,
                previous_menu=MENU_CREATED_TASK,
            )

        if choice == "0":
            if source_task_id:
                return self.support.enter_post_pipeline(
                    repo_path=repo_path,
                    source_task_id=source_task_id,
                    previous_menu=previous_menu,
                    last_message="後工程メニューへ戻りました。",
                )

            return self.support.switch_menu(
                repo_path=repo_path,
                menu=MENU_MAIN,
                last_message="メインメニューへ戻りました。",
                previous_menu=MENU_CREATED_TASK,
            )

        return self.support.stay_with_message(
            repo_path=repo_path,
            menu=MENU_CREATED_TASK,
            last_message="無効な番号です。もう一度選択してください。",
        )

    def handle_post_run(self, *, repo_path: str, choice: str) -> dict:
        store = RemoteSessionStore(repo_path=repo_path)
        payload = store.load()
        task_id = str(payload.get("selected_task_id", "")).strip()
        previous_menu = str(payload.get("previous_menu", MENU_MAIN)).strip() or MENU_MAIN

        if not task_id:
            return self.support.switch_menu(
                repo_path=repo_path,
                menu=MENU_MAIN,
                last_message="選択中 task が見つからないため、メインメニューへ戻しました。",
                previous_menu=MENU_POST_RUN,
            )

        task = StatusUseCase().get_task_status(repo_path=repo_path, task_id=task_id)
        status = str(task.get("status", "")).strip()

        if choice == "0":
            return self.support.switch_menu(
                repo_path=repo_path,
                menu=previous_menu,
                last_message="前の画面へ戻りました。",
                previous_menu=MENU_POST_RUN,
            )

        if status == "completed":
            if choice == "1":
                return self.support.enter_post_pipeline(
                    repo_path=repo_path,
                    source_task_id=task_id,
                    previous_menu=MENU_POST_RUN,
                    last_message=f"{task_id} の後工程メニューへ移動しました。",
                )
            if choice == "2":
                return self.support.switch_menu(
                    repo_path=repo_path,
                    menu=MENU_TASK_LIST,
                    last_message="task 一覧へ移動しました。",
                    previous_menu=MENU_POST_RUN,
                )
            if choice == "3":
                return self.support.switch_menu(
                    repo_path=repo_path,
                    menu=MENU_MAIN,
                    last_message="メインメニューへ戻りました。",
                    previous_menu=MENU_POST_RUN,
                )
            return self.support.stay_with_message(
                repo_path=repo_path,
                menu=MENU_POST_RUN,
                last_message="無効な番号です。もう一度選択してください。",
            )

        if choice == "1":
            return self.support.switch_menu(
                repo_path=repo_path,
                menu=MENU_TASK_LIST,
                last_message="task 一覧へ移動しました。",
                previous_menu=MENU_POST_RUN,
            )

        if choice == "2":
            return self.support.switch_menu(
                repo_path=repo_path,
                menu=MENU_MAIN,
                last_message="メインメニューへ戻りました。",
                previous_menu=MENU_POST_RUN,
            )

        return self.support.stay_with_message(
            repo_path=repo_path,
            menu=MENU_POST_RUN,
            last_message="無効な番号です。もう一度選択してください。",
        )
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
from claude_orchestrator.application.remote_operator.renderer import (
    RemoteOperatorRenderer,
)
from claude_orchestrator.application.usecases.create_task_from_plan_director_usecase import (
    CreateTaskFromPlanDirectorUseCase,
)
from claude_orchestrator.application.usecases.create_task_from_proposal_usecase import (
    CreateTaskFromProposalUseCase,
)
from claude_orchestrator.application.usecases.generate_next_task_proposals_usecase import (
    GenerateNextTaskProposalsUseCase,
)
from claude_orchestrator.application.usecases.list_proposals_usecase import (
    ListProposalsUseCase,
)
from claude_orchestrator.application.usecases.run_plan_director_usecase import (
    RunPlanDirectorUseCase,
)
from claude_orchestrator.application.usecases.run_task_usecase import (
    RunTaskUseCase,
)
from claude_orchestrator.application.usecases.status_usecase import StatusUseCase
from claude_orchestrator.infrastructure.remote_session_store import RemoteSessionStore


class RemoteOperatorController:
    def __init__(self) -> None:
        self.renderer = RemoteOperatorRenderer()

    def show_menu(self, *, repo_path: str) -> dict:
        store = RemoteSessionStore(repo_path=repo_path)
        payload = store.load()
        current_menu = str(payload.get("current_menu", DEFAULT_MENU)).strip() or DEFAULT_MENU
        last_message = str(payload.get("last_message", "")).strip()

        text = self._render_current_menu(
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
            return self._stay_with_message(
                repo_path=repo_path,
                menu=current_menu,
                last_message="無効な入力です。番号で入力してください。",
            )

        if current_menu == MENU_MAIN:
            return self._handle_main_menu(repo_path=repo_path, choice=normalized)

        if current_menu == MENU_IN_PROGRESS_TASK_LIST:
            return self._handle_in_progress_task_list(repo_path=repo_path, choice=normalized)

        if current_menu == MENU_COMPLETED_TASK_LIST:
            return self._handle_completed_task_list(repo_path=repo_path, choice=normalized)

        if current_menu == MENU_TASK_LIST:
            return self._handle_task_list(repo_path=repo_path, choice=normalized)

        if current_menu == MENU_SELECTED_TASK:
            return self._handle_selected_task(repo_path=repo_path, choice=normalized)

        if current_menu == MENU_PROPOSAL_LIST:
            return self._handle_proposal_list(repo_path=repo_path, choice=normalized)

        if current_menu == MENU_SELECTED_PROPOSAL:
            return self._handle_selected_proposal(repo_path=repo_path, choice=normalized)

        if current_menu == MENU_CREATED_TASK:
            return self._handle_created_task(repo_path=repo_path, choice=normalized)

        if current_menu == MENU_POST_RUN:
            return self._handle_post_run(repo_path=repo_path, choice=normalized)

        if current_menu == MENU_POST_PIPELINE:
            return self._handle_post_pipeline(repo_path=repo_path, choice=normalized)

        if current_menu == MENU_PLAN_DIRECTOR_RESULT:
            return self._handle_plan_director_result(repo_path=repo_path, choice=normalized)

        if current_menu == MENU_NEXT_TASK_APPROVAL:
            return self._handle_next_task_approval(repo_path=repo_path, choice=normalized)

        if current_menu == MENU_PIPELINE_SETTINGS:
            return self._handle_pipeline_settings(repo_path=repo_path, choice=normalized)

        if current_menu == MENU_EXITED:
            return self._handle_exited(repo_path=repo_path, choice=normalized)

        store.reset_operator_state()
        return self._render_result(
            repo_path=repo_path,
            menu=MENU_MAIN,
            last_message="メニュー状態が不正だったため、メインメニューへ戻しました。",
        )

    def _handle_main_menu(self, *, repo_path: str, choice: str) -> dict:
        if choice == "1":
            tasks = self._list_in_progress_tasks(repo_path=repo_path)
            if not tasks:
                return self._stay_with_message(
                    repo_path=repo_path,
                    menu=MENU_MAIN,
                    last_message="in_progress task はありません。",
                )
            if len(tasks) == 1:
                task_id = str(tasks[0]["task_id"])
                return self._run_task_and_render(
                    repo_path=repo_path,
                    task_id=task_id,
                    previous_menu=MENU_MAIN,
                )
            return self._switch_menu(
                repo_path=repo_path,
                menu=MENU_IN_PROGRESS_TASK_LIST,
                last_message="実行する in_progress task を選択してください。",
                previous_menu=MENU_MAIN,
            )

        if choice == "2":
            tasks = self._list_completed_tasks(repo_path=repo_path)
            if not tasks:
                return self._stay_with_message(
                    repo_path=repo_path,
                    menu=MENU_MAIN,
                    last_message="completed task はありません。",
                )
            if len(tasks) == 1:
                task_id = str(tasks[0]["task_id"])
                return self._enter_post_pipeline(
                    repo_path=repo_path,
                    source_task_id=task_id,
                    previous_menu=MENU_MAIN,
                    last_message=f"{task_id} の後工程メニューへ移動しました。",
                )
            return self._switch_menu(
                repo_path=repo_path,
                menu=MENU_COMPLETED_TASK_LIST,
                last_message="後工程を操作する completed task を選択してください。",
                previous_menu=MENU_MAIN,
            )

        if choice == "3" or choice == "4":
            return self._switch_menu(
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
            return self._render_result(
                repo_path=repo_path,
                menu=MENU_EXITED,
                last_message="Remote Operator を終了状態にしました。",
            )

        return self._stay_with_message(
            repo_path=repo_path,
            menu=MENU_MAIN,
            last_message="無効な入力です。番号で入力してください。",
        )

    def _handle_in_progress_task_list(self, *, repo_path: str, choice: str) -> dict:
        if choice == "0":
            return self._switch_menu(
                repo_path=repo_path,
                menu=MENU_MAIN,
                last_message="メインメニューへ戻りました。",
                previous_menu=MENU_IN_PROGRESS_TASK_LIST,
            )

        tasks = self._list_in_progress_tasks(repo_path=repo_path)
        selected = self._select_from_numbered_items(tasks, choice)
        if selected is None:
            return self._stay_with_message(
                repo_path=repo_path,
                menu=MENU_IN_PROGRESS_TASK_LIST,
                last_message="無効な番号です。もう一度選択してください。",
            )

        return self._run_task_and_render(
            repo_path=repo_path,
            task_id=str(selected["task_id"]),
            previous_menu=MENU_IN_PROGRESS_TASK_LIST,
        )

    def _handle_completed_task_list(self, *, repo_path: str, choice: str) -> dict:
        if choice == "0":
            return self._switch_menu(
                repo_path=repo_path,
                menu=MENU_MAIN,
                last_message="メインメニューへ戻りました。",
                previous_menu=MENU_COMPLETED_TASK_LIST,
            )

        tasks = self._list_completed_tasks(repo_path=repo_path)
        selected = self._select_from_numbered_items(tasks, choice)
        if selected is None:
            return self._stay_with_message(
                repo_path=repo_path,
                menu=MENU_COMPLETED_TASK_LIST,
                last_message="無効な番号です。もう一度選択してください。",
            )

        return self._enter_post_pipeline(
            repo_path=repo_path,
            source_task_id=str(selected["task_id"]),
            previous_menu=MENU_COMPLETED_TASK_LIST,
            last_message=f"{selected['task_id']} の後工程メニューへ移動しました。",
        )

    def _handle_task_list(self, *, repo_path: str, choice: str) -> dict:
        if choice == "0":
            return self._switch_menu(
                repo_path=repo_path,
                menu=MENU_MAIN,
                last_message="メインメニューへ戻りました。",
                previous_menu=MENU_TASK_LIST,
            )

        tasks = StatusUseCase().list_tasks(repo_path=repo_path)
        selected = self._select_from_numbered_items(tasks, choice)
        if selected is None:
            return self._stay_with_message(
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
            current_menu=MENU_SELECTED_TASK,
            previous_menu=MENU_TASK_LIST,
            last_message=f"{task_id} を選択しました。",
        )
        return self._render_result(
            repo_path=repo_path,
            menu=MENU_SELECTED_TASK,
            last_message=f"{task_id} を選択しました。",
        )

    def _handle_selected_task(self, *, repo_path: str, choice: str) -> dict:
        store = RemoteSessionStore(repo_path=repo_path)
        payload = store.load()
        task_id = str(payload.get("selected_task_id", "")).strip()

        if not task_id:
            return self._switch_menu(
                repo_path=repo_path,
                menu=MENU_TASK_LIST,
                last_message="選択中 task が無いため、task 一覧へ戻しました。",
                previous_menu=MENU_SELECTED_TASK,
            )

        task = StatusUseCase().get_task_status(repo_path=repo_path, task_id=task_id)
        status = str(task.get("status", "")).strip()

        if choice == "1":
            return self._stay_with_message(
                repo_path=repo_path,
                menu=MENU_SELECTED_TASK,
                last_message=f"{task_id} の詳細を再表示します。",
            )

        if choice == "2":
            if status == "in_progress":
                return self._run_task_and_render(
                    repo_path=repo_path,
                    task_id=task_id,
                    previous_menu=MENU_SELECTED_TASK,
                )
            if status == "completed":
                return self._enter_post_pipeline(
                    repo_path=repo_path,
                    source_task_id=task_id,
                    previous_menu=MENU_SELECTED_TASK,
                    last_message=f"{task_id} の後工程メニューへ移動しました。",
                )
            return self._stay_with_message(
                repo_path=repo_path,
                menu=MENU_SELECTED_TASK,
                last_message=(
                    f"{task_id} は status={status} のため、"
                    "この操作は実行できません。"
                ),
            )

        if choice == "3":
            if status == "in_progress":
                return self._run_standard_task_pipeline_and_render(
                    repo_path=repo_path,
                    task_id=task_id,
                    previous_menu=MENU_SELECTED_TASK,
                )
            if status == "completed":
                return self._run_post_pipeline_auto_and_render(
                    repo_path=repo_path,
                    source_task_id=task_id,
                    previous_menu=MENU_SELECTED_TASK,
                )
            return self._stay_with_message(
                repo_path=repo_path,
                menu=MENU_SELECTED_TASK,
                last_message=(
                    f"{task_id} は status={status} のため、"
                    "この操作は実行できません。"
                ),
            )

        if choice == "0":
            return self._switch_menu(
                repo_path=repo_path,
                menu=MENU_TASK_LIST,
                last_message="task 一覧へ戻りました。",
                previous_menu=MENU_SELECTED_TASK,
            )

        return self._stay_with_message(
            repo_path=repo_path,
            menu=MENU_SELECTED_TASK,
            last_message="無効な番号です。もう一度選択してください。",
        )

    def _handle_proposal_list(self, *, repo_path: str, choice: str) -> dict:
        store = RemoteSessionStore(repo_path=repo_path)
        payload = store.load()
        source_task_id = str(payload.get("selected_source_task_id", "")).strip()
        if not source_task_id:
            source_task_id = str(payload.get("selected_task_id", "")).strip()

        if not source_task_id:
            return self._switch_menu(
                repo_path=repo_path,
                menu=MENU_MAIN,
                last_message="source task が見つからないため、メインメニューへ戻しました。",
                previous_menu=MENU_PROPOSAL_LIST,
            )

        if choice == "0":
            return self._enter_post_pipeline(
                repo_path=repo_path,
                source_task_id=source_task_id,
                previous_menu=MENU_PROPOSAL_LIST,
                last_message=f"{source_task_id} の後工程メニューへ戻りました。",
            )

        result = ListProposalsUseCase().execute(
            repo_path=repo_path,
            source_task_id=source_task_id,
        )
        proposals = result["proposals"]
        selected = self._select_from_numbered_items(proposals, choice)
        if selected is None:
            return self._stay_with_message(
                repo_path=repo_path,
                menu=MENU_PROPOSAL_LIST,
                last_message="無効な番号です。もう一度選択してください。",
            )

        proposal_id = str(selected["proposal_id"]).strip()
        store.update_fields(
            selected_source_task_id=source_task_id,
            selected_proposal_id=proposal_id,
            current_menu=MENU_SELECTED_PROPOSAL,
            previous_menu=MENU_PROPOSAL_LIST,
            last_message=f"{proposal_id} を選択しました。",
        )
        return self._render_result(
            repo_path=repo_path,
            menu=MENU_SELECTED_PROPOSAL,
            last_message=f"{proposal_id} を選択しました。",
        )

    def _handle_selected_proposal(self, *, repo_path: str, choice: str) -> dict:
        store = RemoteSessionStore(repo_path=repo_path)
        payload = store.load()
        source_task_id = str(payload.get("selected_source_task_id", "")).strip()
        proposal_id = str(payload.get("selected_proposal_id", "")).strip()

        if not source_task_id or not proposal_id:
            return self._switch_menu(
                repo_path=repo_path,
                menu=MENU_PROPOSAL_LIST,
                last_message="proposal 選択状態が無いため、proposal 一覧へ戻しました。",
                previous_menu=MENU_SELECTED_PROPOSAL,
            )

        if choice == "1":
            result = CreateTaskFromProposalUseCase().execute(
                repo_path=repo_path,
                source_task_id=source_task_id,
                proposal_id=proposal_id,
            )
            created_task_id = str(result["created_task_id"]).strip()
            store.update_fields(
                selected_task_id=created_task_id,
                selected_source_task_id=source_task_id,
                selected_proposal_id=proposal_id,
                current_menu=MENU_CREATED_TASK,
                previous_menu=MENU_SELECTED_PROPOSAL,
                last_message=f"{proposal_id} から {created_task_id} を作成しました。",
            )
            return self._render_result(
                repo_path=repo_path,
                menu=MENU_CREATED_TASK,
                last_message=f"{proposal_id} から {created_task_id} を作成しました。",
            )

        if choice == "0":
            store.update_fields(
                current_menu=MENU_PROPOSAL_LIST,
                previous_menu=MENU_SELECTED_PROPOSAL,
                last_message=f"{source_task_id} の proposal 一覧へ戻りました。",
            )
            return self._render_result(
                repo_path=repo_path,
                menu=MENU_PROPOSAL_LIST,
                last_message=f"{source_task_id} の proposal 一覧へ戻りました。",
            )

        return self._stay_with_message(
            repo_path=repo_path,
            menu=MENU_SELECTED_PROPOSAL,
            last_message="無効な番号です。もう一度選択してください。",
        )

    def _handle_created_task(self, *, repo_path: str, choice: str) -> dict:
        store = RemoteSessionStore(repo_path=repo_path)
        payload = store.load()
        task_id = str(payload.get("selected_task_id", "")).strip()
        source_task_id = str(payload.get("selected_source_task_id", "")).strip()
        previous_menu = str(payload.get("previous_menu", MENU_MAIN)).strip() or MENU_MAIN

        if not task_id:
            return self._switch_menu(
                repo_path=repo_path,
                menu=MENU_MAIN,
                last_message="作成済み task が見つからないため、メインメニューへ戻しました。",
                previous_menu=MENU_CREATED_TASK,
            )

        if choice == "1":
            return self._run_task_and_render(
                repo_path=repo_path,
                task_id=task_id,
                previous_menu=MENU_CREATED_TASK,
            )

        if choice == "0":
            if previous_menu in {
                MENU_NEXT_TASK_APPROVAL,
                MENU_PLAN_DIRECTOR_RESULT,
                MENU_POST_PIPELINE,
                MENU_SELECTED_TASK,
            } and source_task_id:
                return self._enter_post_pipeline(
                    repo_path=repo_path,
                    source_task_id=source_task_id,
                    previous_menu=MENU_CREATED_TASK,
                    last_message=f"{source_task_id} の後工程メニューへ戻りました。",
                )

            if previous_menu == MENU_SELECTED_PROPOSAL:
                store.update_fields(
                    current_menu=MENU_SELECTED_PROPOSAL,
                    previous_menu=MENU_CREATED_TASK,
                    last_message="proposal 選択画面へ戻りました。",
                )
                return self._render_result(
                    repo_path=repo_path,
                    menu=MENU_SELECTED_PROPOSAL,
                    last_message="proposal 選択画面へ戻りました。",
                )

            return self._switch_menu(
                repo_path=repo_path,
                menu=MENU_MAIN,
                last_message="メインメニューへ戻りました。",
                previous_menu=MENU_CREATED_TASK,
            )

        return self._stay_with_message(
            repo_path=repo_path,
            menu=MENU_CREATED_TASK,
            last_message="無効な番号です。もう一度選択してください。",
        )

    def _handle_post_run(self, *, repo_path: str, choice: str) -> dict:
        store = RemoteSessionStore(repo_path=repo_path)
        payload = store.load()
        task_id = str(payload.get("selected_task_id", "")).strip()
        previous_menu = str(payload.get("previous_menu", MENU_MAIN)).strip() or MENU_MAIN

        if not task_id:
            return self._switch_menu(
                repo_path=repo_path,
                menu=MENU_MAIN,
                last_message="選択中 task が見つからないため、メインメニューへ戻しました。",
                previous_menu=MENU_POST_RUN,
            )

        task = StatusUseCase().get_task_status(repo_path=repo_path, task_id=task_id)
        status = str(task.get("status", "")).strip()

        if choice == "0":
            return self._switch_menu(
                repo_path=repo_path,
                menu=previous_menu,
                last_message="前の画面へ戻りました。",
                previous_menu=MENU_POST_RUN,
            )

        if status == "completed":
            if choice == "1":
                return self._enter_post_pipeline(
                    repo_path=repo_path,
                    source_task_id=task_id,
                    previous_menu=MENU_POST_RUN,
                    last_message=f"{task_id} の後工程メニューへ移動しました。",
                )
            if choice == "2":
                return self._switch_menu(
                    repo_path=repo_path,
                    menu=MENU_TASK_LIST,
                    last_message="task 一覧へ移動しました。",
                    previous_menu=MENU_POST_RUN,
                )
            if choice == "3":
                return self._switch_menu(
                    repo_path=repo_path,
                    menu=MENU_MAIN,
                    last_message="メインメニューへ戻りました。",
                    previous_menu=MENU_POST_RUN,
                )
            return self._stay_with_message(
                repo_path=repo_path,
                menu=MENU_POST_RUN,
                last_message="無効な番号です。もう一度選択してください。",
            )

        if choice == "1":
            return self._switch_menu(
                repo_path=repo_path,
                menu=MENU_TASK_LIST,
                last_message="task 一覧へ移動しました。",
                previous_menu=MENU_POST_RUN,
            )

        if choice == "2":
            return self._switch_menu(
                repo_path=repo_path,
                menu=MENU_MAIN,
                last_message="メインメニューへ戻りました。",
                previous_menu=MENU_POST_RUN,
            )

        return self._stay_with_message(
            repo_path=repo_path,
            menu=MENU_POST_RUN,
            last_message="無効な番号です。もう一度選択してください。",
        )

    def _handle_post_pipeline(self, *, repo_path: str, choice: str) -> dict:
        store = RemoteSessionStore(repo_path=repo_path)
        payload = store.load()
        source_task_id = self._get_post_pipeline_source_task_id(repo_path=repo_path)
        previous_menu = str(payload.get("previous_menu", MENU_MAIN)).strip() or MENU_MAIN

        if not source_task_id:
            return self._switch_menu(
                repo_path=repo_path,
                menu=MENU_MAIN,
                last_message="source task が見つからないため、メインメニューへ戻しました。",
                previous_menu=MENU_POST_PIPELINE,
            )

        if choice == "1":
            planner_role = self._get_last_planner_role(repo_path=repo_path)
            GenerateNextTaskProposalsUseCase().execute(
                repo_path=repo_path,
                source_task_id=source_task_id,
                reference_doc_paths=[],
                planner_role=planner_role,
            )

            store.update_fields(
                selected_task_id=source_task_id,
                selected_source_task_id=source_task_id,
                selected_proposal_id="",
                post_run_source_task_id=source_task_id,
                current_menu=MENU_PROPOSAL_LIST,
                previous_menu=MENU_POST_PIPELINE,
                last_planner_role=planner_role,
                waiting_next_task_approval=False,
                last_plan_director_decision="",
                last_plan_director_selected_proposal_id="",
                last_plan_director_selection_reason="",
                last_message=(
                    f"{source_task_id} の planner ({planner_role}) を実行し、"
                    "次タスク案を作成しました。"
                ),
            )
            return self._render_result(
                repo_path=repo_path,
                menu=MENU_PROPOSAL_LIST,
                last_message=(
                    f"{source_task_id} の planner ({planner_role}) を実行し、"
                    "次タスク案を作成しました。"
                ),
            )

        if choice == "2":
            return self._run_plan_director_and_render(
                repo_path=repo_path,
                source_task_id=source_task_id,
                previous_menu=MENU_POST_PIPELINE,
            )

        if choice == "3":
            return self._run_post_pipeline_auto_and_render(
                repo_path=repo_path,
                source_task_id=source_task_id,
                previous_menu=MENU_POST_PIPELINE,
            )

        if choice == "4":
            if not bool(payload.get("waiting_next_task_approval", False)):
                return self._stay_with_message(
                    repo_path=repo_path,
                    menu=MENU_POST_PIPELINE,
                    last_message="現在、承認待ち案件はありません。",
                )
            return self._switch_menu(
                repo_path=repo_path,
                menu=MENU_NEXT_TASK_APPROVAL,
                last_message="承認待ち画面へ移動しました。",
                previous_menu=MENU_POST_PIPELINE,
            )

        if choice == "5":
            return self._switch_menu(
                repo_path=repo_path,
                menu=MENU_PIPELINE_SETTINGS,
                last_message="pipeline 設定へ移動しました。",
                previous_menu=MENU_POST_PIPELINE,
            )

        if choice == "6":
            return self._switch_menu(
                repo_path=repo_path,
                menu=MENU_TASK_LIST,
                last_message="task 一覧へ移動しました。",
                previous_menu=MENU_POST_PIPELINE,
            )

        if choice == "7":
            return self._switch_menu(
                repo_path=repo_path,
                menu=MENU_MAIN,
                last_message="メインメニューへ戻りました。",
                previous_menu=MENU_POST_PIPELINE,
            )

        if choice == "0":
            return self._switch_menu(
                repo_path=repo_path,
                menu=previous_menu,
                last_message="前の画面へ戻りました。",
                previous_menu=MENU_POST_PIPELINE,
            )

        return self._stay_with_message(
            repo_path=repo_path,
            menu=MENU_POST_PIPELINE,
            last_message="無効な番号です。もう一度選択してください。",
        )

    def _handle_plan_director_result(self, *, repo_path: str, choice: str) -> dict:
        store = RemoteSessionStore(repo_path=repo_path)
        payload = store.load()
        source_task_id = self._get_post_pipeline_source_task_id(repo_path=repo_path)
        decision = str(payload.get("last_plan_director_decision", "")).strip()
        approval_mode = self._get_approval_mode(repo_path=repo_path)

        if not source_task_id:
            return self._switch_menu(
                repo_path=repo_path,
                menu=MENU_MAIN,
                last_message="source task が見つからないため、メインメニューへ戻しました。",
                previous_menu=MENU_PLAN_DIRECTOR_RESULT,
            )

        if choice == "0":
            return self._enter_post_pipeline(
                repo_path=repo_path,
                source_task_id=source_task_id,
                previous_menu=MENU_PLAN_DIRECTOR_RESULT,
                last_message=f"{source_task_id} の後工程メニューへ戻りました。",
            )

        if decision == "adopt":
            if choice == "1":
                if approval_mode == "auto":
                    return self._create_task_from_plan_director_and_render(
                        repo_path=repo_path,
                        source_task_id=source_task_id,
                        previous_menu=MENU_PLAN_DIRECTOR_RESULT,
                    )
                store.update_fields(
                    waiting_next_task_approval=True,
                    current_menu=MENU_NEXT_TASK_APPROVAL,
                    previous_menu=MENU_PLAN_DIRECTOR_RESULT,
                    last_message="次 task 承認待ちへ移動しました。",
                )
                return self._render_result(
                    repo_path=repo_path,
                    menu=MENU_NEXT_TASK_APPROVAL,
                    last_message="次 task 承認待ちへ移動しました。",
                )

            if choice == "2":
                return self._enter_post_pipeline(
                    repo_path=repo_path,
                    source_task_id=source_task_id,
                    previous_menu=MENU_PLAN_DIRECTOR_RESULT,
                    last_message=f"{source_task_id} の後工程メニューへ戻りました。",
                )

            if choice == "3":
                return self._switch_menu(
                    repo_path=repo_path,
                    menu=MENU_TASK_LIST,
                    last_message="task 一覧へ移動しました。",
                    previous_menu=MENU_PLAN_DIRECTOR_RESULT,
                )

            return self._stay_with_message(
                repo_path=repo_path,
                menu=MENU_PLAN_DIRECTOR_RESULT,
                last_message="無効な番号です。もう一度選択してください。",
            )

        if choice == "1":
            return self._enter_post_pipeline(
                repo_path=repo_path,
                source_task_id=source_task_id,
                previous_menu=MENU_PLAN_DIRECTOR_RESULT,
                last_message=f"{source_task_id} の後工程メニューへ戻りました。",
            )

        if choice == "2":
            return self._switch_menu(
                repo_path=repo_path,
                menu=MENU_TASK_LIST,
                last_message="task 一覧へ移動しました。",
                previous_menu=MENU_PLAN_DIRECTOR_RESULT,
            )

        return self._stay_with_message(
            repo_path=repo_path,
            menu=MENU_PLAN_DIRECTOR_RESULT,
            last_message="無効な番号です。もう一度選択してください。",
        )

    def _handle_next_task_approval(self, *, repo_path: str, choice: str) -> dict:
        store = RemoteSessionStore(repo_path=repo_path)
        payload = store.load()
        source_task_id = self._get_post_pipeline_source_task_id(repo_path=repo_path)
        decision = str(payload.get("last_plan_director_decision", "")).strip()

        if not source_task_id:
            return self._switch_menu(
                repo_path=repo_path,
                menu=MENU_MAIN,
                last_message="source task が見つからないため、メインメニューへ戻しました。",
                previous_menu=MENU_NEXT_TASK_APPROVAL,
            )

        if decision != "adopt":
            return self._enter_post_pipeline(
                repo_path=repo_path,
                source_task_id=source_task_id,
                previous_menu=MENU_NEXT_TASK_APPROVAL,
                last_message="adopt 状態ではないため、後工程メニューへ戻しました。",
            )

        if choice == "1":
            return self._create_task_from_plan_director_and_render(
                repo_path=repo_path,
                source_task_id=source_task_id,
                previous_menu=MENU_NEXT_TASK_APPROVAL,
            )

        if choice == "2":
            store.update_fields(
                waiting_next_task_approval=False,
                current_menu=MENU_POST_PIPELINE,
                previous_menu=MENU_NEXT_TASK_APPROVAL,
                last_message="今回は次 task を作成しないことにしました。",
            )
            return self._render_result(
                repo_path=repo_path,
                menu=MENU_POST_PIPELINE,
                last_message="今回は次 task を作成しないことにしました。",
            )

        if choice == "3" or choice == "0":
            return self._enter_post_pipeline(
                repo_path=repo_path,
                source_task_id=source_task_id,
                previous_menu=MENU_NEXT_TASK_APPROVAL,
                last_message=f"{source_task_id} の後工程メニューへ戻りました。",
            )

        return self._stay_with_message(
            repo_path=repo_path,
            menu=MENU_NEXT_TASK_APPROVAL,
            last_message="無効な番号です。もう一度選択してください。",
        )

    def _handle_pipeline_settings(self, *, repo_path: str, choice: str) -> dict:
        store = RemoteSessionStore(repo_path=repo_path)
        payload = store.load()

        if choice == "1":
            store.update_fields(
                approval_mode="manual",
                current_menu=MENU_PIPELINE_SETTINGS,
                last_message="approval_mode を manual にしました。",
            )
            return self._render_result(
                repo_path=repo_path,
                menu=MENU_PIPELINE_SETTINGS,
                last_message="approval_mode を manual にしました。",
            )

        if choice == "2":
            store.update_fields(
                approval_mode="auto",
                current_menu=MENU_PIPELINE_SETTINGS,
                last_message="approval_mode を auto にしました。",
            )
            return self._render_result(
                repo_path=repo_path,
                menu=MENU_PIPELINE_SETTINGS,
                last_message="approval_mode を auto にしました。",
            )

        if choice == "3":
            current_value = bool(payload.get("stop_after_current_task_requested", False))
            next_value = not current_value
            store.update_fields(
                stop_after_current_task_requested=next_value,
                current_menu=MENU_PIPELINE_SETTINGS,
                last_message=(
                    "stop reservation を "
                    f"{'ON' if next_value else 'OFF'} にしました。"
                ),
            )
            return self._render_result(
                repo_path=repo_path,
                menu=MENU_PIPELINE_SETTINGS,
                last_message=(
                    "stop reservation を "
                    f"{'ON' if next_value else 'OFF'} にしました。"
                ),
            )

        if choice == "0":
            return self._switch_menu(
                repo_path=repo_path,
                menu=MENU_POST_PIPELINE,
                last_message="後工程メニューへ戻りました。",
                previous_menu=MENU_PIPELINE_SETTINGS,
            )

        return self._stay_with_message(
            repo_path=repo_path,
            menu=MENU_PIPELINE_SETTINGS,
            last_message="無効な番号です。もう一度選択してください。",
        )

    def _handle_exited(self, *, repo_path: str, choice: str) -> dict:
        if choice == "0":
            return self._switch_menu(
                repo_path=repo_path,
                menu=MENU_MAIN,
                last_message="メインメニューへ戻りました。",
                previous_menu=MENU_EXITED,
            )

        return self._stay_with_message(
            repo_path=repo_path,
            menu=MENU_EXITED,
            last_message="終了状態です。0 を入力するとメインメニューへ戻ります。",
        )

    def _run_task_and_render(
        self,
        *,
        repo_path: str,
        task_id: str,
        previous_menu: str,
    ) -> dict:
        result = RunTaskUseCase().execute(
            repo_path=repo_path,
            task_id=task_id,
        )
        status = str(result["status"]).strip()
        cycle = str(result["cycle"]).strip()
        next_role = str(result["next_role"]).strip()

        message = (
            f"{task_id} 実行完了\n"
            f"status={status}\n"
            f"cycle={cycle}\n"
            f"next_role={next_role}"
        )

        if status == "completed":
            return self._enter_post_pipeline(
                repo_path=repo_path,
                source_task_id=task_id,
                previous_menu=previous_menu,
                last_message=message,
            )

        store = RemoteSessionStore(repo_path=repo_path)
        store.update_fields(
            selected_task_id=task_id,
            current_menu=MENU_POST_RUN,
            previous_menu=previous_menu,
            last_message=message,
        )
        return self._render_result(
            repo_path=repo_path,
            menu=MENU_POST_RUN,
            last_message=message,
        )

    def _run_standard_task_pipeline_and_render(
        self,
        *,
        repo_path: str,
        task_id: str,
        previous_menu: str,
    ) -> dict:
        run_result = RunTaskUseCase().execute(
            repo_path=repo_path,
            task_id=task_id,
        )
        status = str(run_result["status"]).strip()
        cycle = str(run_result["cycle"]).strip()
        next_role = str(run_result["next_role"]).strip()

        run_message = (
            f"{task_id} 実行完了\n"
            f"status={status}\n"
            f"cycle={cycle}\n"
            f"next_role={next_role}"
        )

        if status != "completed":
            store = RemoteSessionStore(repo_path=repo_path)
            store.update_fields(
                selected_task_id=task_id,
                current_menu=MENU_POST_RUN,
                previous_menu=previous_menu,
                last_message=run_message,
            )
            return self._render_result(
                repo_path=repo_path,
                menu=MENU_POST_RUN,
                last_message=run_message,
            )

        return self._run_post_pipeline_auto_and_render(
            repo_path=repo_path,
            source_task_id=task_id,
            previous_menu=previous_menu,
            preface_message=run_message,
        )

    def _run_post_pipeline_auto_and_render(
        self,
        *,
        repo_path: str,
        source_task_id: str,
        previous_menu: str,
        preface_message: str = "",
    ) -> dict:
        planner_role = self._get_last_planner_role(repo_path=repo_path)

        GenerateNextTaskProposalsUseCase().execute(
            repo_path=repo_path,
            source_task_id=source_task_id,
            reference_doc_paths=[],
            planner_role=planner_role,
        )

        plan_result = RunPlanDirectorUseCase().execute(
            repo_path=repo_path,
            source_task_id=source_task_id,
        )
        report = dict(plan_result.get("plan_director_report", {}) or {})
        decision = str(report.get("decision", "")).strip()
        selected_proposal_id = str(report.get("selected_proposal_id", "")).strip()
        selection_reason = str(report.get("selection_reason", "")).strip()
        selected_planner_role = str(
            report.get("selected_planner_role", "")
        ).strip() or planner_role
        approval_mode = self._get_approval_mode(repo_path=repo_path)

        store = RemoteSessionStore(repo_path=repo_path)
        waiting_next_task_approval = decision == "adopt" and approval_mode == "manual"
        auto_message = (
            f"{source_task_id} の planner ({selected_planner_role}) → "
            f"plan_director を自動実行しました。 decision={decision or '-'}"
        )
        final_message = auto_message
        if preface_message:
            final_message = f"{preface_message}\n\n{auto_message}"

        store.update_fields(
            selected_task_id=source_task_id,
            selected_source_task_id=source_task_id,
            selected_proposal_id="",
            post_run_source_task_id=source_task_id,
            last_plan_director_decision=decision,
            last_plan_director_selected_proposal_id=selected_proposal_id,
            last_plan_director_selection_reason=selection_reason,
            last_planner_role=selected_planner_role or "planner_safe",
            waiting_next_task_approval=waiting_next_task_approval,
            last_message=final_message,
        )

        if decision == "adopt" and approval_mode == "auto":
            return self._create_task_from_plan_director_and_render(
                repo_path=repo_path,
                source_task_id=source_task_id,
                previous_menu=previous_menu,
                message_prefix=final_message,
            )

        next_menu = MENU_PLAN_DIRECTOR_RESULT
        if decision == "adopt" and approval_mode == "manual":
            next_menu = MENU_NEXT_TASK_APPROVAL

        store.update_fields(
            current_menu=next_menu,
            previous_menu=previous_menu,
        )
        return self._render_result(
            repo_path=repo_path,
            menu=next_menu,
            last_message=final_message,
        )

    def _run_plan_director_and_render(
        self,
        *,
        repo_path: str,
        source_task_id: str,
        previous_menu: str,
    ) -> dict:
        result = RunPlanDirectorUseCase().execute(
            repo_path=repo_path,
            source_task_id=source_task_id,
        )
        report = dict(result.get("plan_director_report", {}) or {})
        decision = str(report.get("decision", "")).strip()
        selected_proposal_id = str(report.get("selected_proposal_id", "")).strip()
        selection_reason = str(report.get("selection_reason", "")).strip()
        selected_planner_role = str(
            report.get("selected_planner_role", "")
        ).strip() or self._get_last_planner_role(repo_path=repo_path)

        approval_mode = self._get_approval_mode(repo_path=repo_path)

        store = RemoteSessionStore(repo_path=repo_path)
        store.update_fields(
            selected_task_id=source_task_id,
            selected_source_task_id=source_task_id,
            post_run_source_task_id=source_task_id,
            last_plan_director_decision=decision,
            last_plan_director_selected_proposal_id=selected_proposal_id,
            last_plan_director_selection_reason=selection_reason,
            last_planner_role=selected_planner_role or "planner_safe",
            waiting_next_task_approval=(decision == "adopt" and approval_mode == "manual"),
            current_menu=MENU_PLAN_DIRECTOR_RESULT,
            previous_menu=previous_menu,
            last_message=(
                f"{source_task_id} の plan_director を実行しました。"
                f" decision={decision or '-'}"
            ),
        )
        return self._render_result(
            repo_path=repo_path,
            menu=MENU_PLAN_DIRECTOR_RESULT,
            last_message=(
                f"{source_task_id} の plan_director を実行しました。"
                f" decision={decision or '-'}"
            ),
        )

    def _enter_post_pipeline(
        self,
        *,
        repo_path: str,
        source_task_id: str,
        previous_menu: str,
        last_message: str,
    ) -> dict:
        store = RemoteSessionStore(repo_path=repo_path)
        store.update_fields(
            selected_task_id=source_task_id,
            selected_source_task_id=source_task_id,
            post_run_source_task_id=source_task_id,
            current_menu=MENU_POST_PIPELINE,
            previous_menu=previous_menu,
            last_message=last_message,
        )
        return self._render_result(
            repo_path=repo_path,
            menu=MENU_POST_PIPELINE,
            last_message=last_message,
        )

    def _create_task_from_plan_director_and_render(
        self,
        *,
        repo_path: str,
        source_task_id: str,
        previous_menu: str,
        message_prefix: str = "",
    ) -> dict:
        result = CreateTaskFromPlanDirectorUseCase().execute(
            repo_path=repo_path,
            source_task_id=source_task_id,
        )
        created_task_id = str(result.get("created_task_id") or "").strip()
        decision = str(result.get("decision", "")).strip()

        if not result.get("created", False) or not created_task_id:
            message = f"次 task は作成されませんでした。 decision={decision or '-'}"
            if message_prefix:
                message = f"{message_prefix}\n\n{message}"
            return self._enter_post_pipeline(
                repo_path=repo_path,
                source_task_id=source_task_id,
                previous_menu=previous_menu,
                last_message=message,
            )

        message = f"{source_task_id} から {created_task_id} を作成しました。"
        if message_prefix:
            message = f"{message_prefix}\n\n{message}"

        store = RemoteSessionStore(repo_path=repo_path)
        store.update_fields(
            selected_task_id=created_task_id,
            selected_source_task_id=source_task_id,
            current_menu=MENU_CREATED_TASK,
            previous_menu=previous_menu,
            waiting_next_task_approval=False,
            last_message=message,
        )
        return self._render_result(
            repo_path=repo_path,
            menu=MENU_CREATED_TASK,
            last_message=message,
        )

    def _render_current_menu(
        self,
        *,
        repo_path: str,
        current_menu: str,
        last_message: str,
    ) -> str:
        if current_menu == MENU_MAIN:
            return self.renderer.render_main_menu(last_message=last_message)

        if current_menu == MENU_IN_PROGRESS_TASK_LIST:
            return self.renderer.render_task_list_menu(
                title="実行する in_progress task を選択してください",
                tasks=self._list_in_progress_tasks(repo_path=repo_path),
                last_message=last_message,
            )

        if current_menu == MENU_COMPLETED_TASK_LIST:
            return self.renderer.render_task_list_menu(
                title="後工程を操作する completed task を選択してください",
                tasks=self._list_completed_tasks(repo_path=repo_path),
                last_message=last_message,
            )

        if current_menu == MENU_TASK_LIST:
            return self.renderer.render_task_list_menu(
                title="task 一覧",
                tasks=StatusUseCase().list_tasks(repo_path=repo_path),
                last_message=last_message,
            )

        if current_menu == MENU_SELECTED_TASK:
            task = self._get_selected_task(repo_path=repo_path)
            return self.renderer.render_selected_task_menu(
                task=task,
                last_message=last_message,
            )

        if current_menu == MENU_PROPOSAL_LIST:
            source_task_id = self._get_selected_source_task_id(repo_path=repo_path)
            proposals = self._get_proposals(
                repo_path=repo_path,
                source_task_id=source_task_id,
            )
            return self.renderer.render_proposal_list_menu(
                source_task_id=source_task_id,
                proposals=proposals,
                last_message=last_message,
            )

        if current_menu == MENU_SELECTED_PROPOSAL:
            source_task_id = self._get_selected_source_task_id(repo_path=repo_path)
            proposal_id = self._get_selected_proposal_id(repo_path=repo_path)
            proposal = self._find_proposal(
                proposals=self._get_proposals(
                    repo_path=repo_path,
                    source_task_id=source_task_id,
                ),
                proposal_id=proposal_id,
            )
            return self.renderer.render_selected_proposal_menu(
                proposal_id=proposal_id,
                proposal=proposal,
                last_message=last_message,
            )

        if current_menu == MENU_CREATED_TASK:
            created_task_id = self._get_selected_task_id(repo_path=repo_path)
            return self.renderer.render_created_task_menu(
                created_task_id=created_task_id,
                last_message=last_message,
            )

        if current_menu == MENU_POST_RUN:
            task_id = self._get_selected_task_id(repo_path=repo_path)
            status = ""
            if task_id:
                task = StatusUseCase().get_task_status(repo_path=repo_path, task_id=task_id)
                status = str(task.get("status", "")).strip()
            return self.renderer.render_post_run_menu(
                task_id=task_id,
                status=status,
                last_message=last_message,
            )

        if current_menu == MENU_POST_PIPELINE:
            source_task_id = self._get_post_pipeline_source_task_id(repo_path=repo_path)
            task_status = ""
            if source_task_id:
                task = StatusUseCase().get_task_status(
                    repo_path=repo_path,
                    task_id=source_task_id,
                )
                task_status = str(task.get("status", "")).strip()
            return self.renderer.render_post_pipeline_menu(
                source_task_id=source_task_id,
                source_task_status=task_status,
                approval_mode=self._get_approval_mode(repo_path=repo_path),
                stop_after_current_task_requested=self._get_stop_reservation(
                    repo_path=repo_path
                ),
                last_planner_role=self._get_last_planner_role(repo_path=repo_path),
                last_plan_director_decision=self._get_last_plan_director_decision(
                    repo_path=repo_path
                ),
                waiting_next_task_approval=self._get_waiting_next_task_approval(
                    repo_path=repo_path
                ),
                last_message=last_message,
            )

        if current_menu == MENU_PLAN_DIRECTOR_RESULT:
            return self.renderer.render_plan_director_result_menu(
                source_task_id=self._get_post_pipeline_source_task_id(repo_path=repo_path),
                decision=self._get_last_plan_director_decision(repo_path=repo_path),
                selected_proposal_id=self._get_last_plan_director_selected_proposal_id(
                    repo_path=repo_path
                ),
                selected_planner_role=self._get_last_planner_role(repo_path=repo_path),
                selection_reason=self._get_last_plan_director_selection_reason(
                    repo_path=repo_path
                ),
                approval_mode=self._get_approval_mode(repo_path=repo_path),
                waiting_next_task_approval=self._get_waiting_next_task_approval(
                    repo_path=repo_path
                ),
                last_message=last_message,
            )

        if current_menu == MENU_NEXT_TASK_APPROVAL:
            return self.renderer.render_next_task_approval_menu(
                source_task_id=self._get_post_pipeline_source_task_id(repo_path=repo_path),
                decision=self._get_last_plan_director_decision(repo_path=repo_path),
                selected_proposal_id=self._get_last_plan_director_selected_proposal_id(
                    repo_path=repo_path
                ),
                selected_planner_role=self._get_last_planner_role(repo_path=repo_path),
                selection_reason=self._get_last_plan_director_selection_reason(
                    repo_path=repo_path
                ),
                last_message=last_message,
            )

        if current_menu == MENU_PIPELINE_SETTINGS:
            return self.renderer.render_pipeline_settings_menu(
                approval_mode=self._get_approval_mode(repo_path=repo_path),
                stop_after_current_task_requested=self._get_stop_reservation(
                    repo_path=repo_path
                ),
                last_message=last_message,
            )

        if current_menu == MENU_EXITED:
            return self.renderer.render_exited_menu(last_message=last_message)

        return self.renderer.render_main_menu(
            last_message="メニュー状態が不正なため、メインメニューを表示します。"
        )

    def _switch_menu(
        self,
        *,
        repo_path: str,
        menu: str,
        last_message: str,
        previous_menu: str,
    ) -> dict:
        store = RemoteSessionStore(repo_path=repo_path)
        store.update_fields(
            current_menu=menu,
            previous_menu=previous_menu,
            last_message=last_message,
        )
        return self._render_result(
            repo_path=repo_path,
            menu=menu,
            last_message=last_message,
        )

    def _stay_with_message(
        self,
        *,
        repo_path: str,
        menu: str,
        last_message: str,
    ) -> dict:
        store = RemoteSessionStore(repo_path=repo_path)
        store.update_fields(
            current_menu=menu,
            last_message=last_message,
        )
        return self._render_result(
            repo_path=repo_path,
            menu=menu,
            last_message=last_message,
        )

    def _render_result(
        self,
        *,
        repo_path: str,
        menu: str,
        last_message: str,
    ) -> dict:
        return {
            "menu": menu,
            "text": self._render_current_menu(
                repo_path=repo_path,
                current_menu=menu,
                last_message=last_message,
            ),
        }

    @staticmethod
    def _select_from_numbered_items(items: list[dict], choice: str) -> dict | None:
        try:
            index = int(choice)
        except ValueError:
            return None

        if index < 1 or index > len(items):
            return None
        return items[index - 1]

    @staticmethod
    def _list_in_progress_tasks(*, repo_path: str) -> list[dict]:
        tasks = StatusUseCase().list_tasks(repo_path=repo_path)
        return [task for task in tasks if str(task.get("status")) == "in_progress"]

    @staticmethod
    def _list_completed_tasks(*, repo_path: str) -> list[dict]:
        tasks = StatusUseCase().list_tasks(repo_path=repo_path)
        return [task for task in tasks if str(task.get("status")) == "completed"]

    @staticmethod
    def _find_proposal(*, proposals: list[dict], proposal_id: str) -> dict | None:
        normalized = str(proposal_id).strip()
        for proposal in proposals:
            if str(proposal.get("proposal_id", "")).strip() == normalized:
                return proposal
        return None

    @staticmethod
    def _get_proposals(*, repo_path: str, source_task_id: str) -> list[dict]:
        if not source_task_id:
            return []
        result = ListProposalsUseCase().execute(
            repo_path=repo_path,
            source_task_id=source_task_id,
        )
        return list(result.get("proposals", []) or [])

    @staticmethod
    def _get_selected_task(repo_path: str) -> dict | None:
        task_id = RemoteOperatorController._get_selected_task_id(repo_path=repo_path)
        if not task_id:
            return None
        return StatusUseCase().get_task_status(repo_path=repo_path, task_id=task_id)

    @staticmethod
    def _get_selected_task_id(*, repo_path: str) -> str:
        store = RemoteSessionStore(repo_path=repo_path)
        payload = store.load()
        return str(payload.get("selected_task_id", "")).strip()

    @staticmethod
    def _get_selected_source_task_id(*, repo_path: str) -> str:
        store = RemoteSessionStore(repo_path=repo_path)
        payload = store.load()
        source_task_id = str(payload.get("selected_source_task_id", "")).strip()
        if source_task_id:
            return source_task_id
        return str(payload.get("selected_task_id", "")).strip()

    @staticmethod
    def _get_post_pipeline_source_task_id(*, repo_path: str) -> str:
        store = RemoteSessionStore(repo_path=repo_path)
        payload = store.load()

        post_run_source_task_id = str(payload.get("post_run_source_task_id", "")).strip()
        if post_run_source_task_id:
            return post_run_source_task_id

        source_task_id = str(payload.get("selected_source_task_id", "")).strip()
        if source_task_id:
            return source_task_id

        return str(payload.get("selected_task_id", "")).strip()

    @staticmethod
    def _get_selected_proposal_id(*, repo_path: str) -> str:
        store = RemoteSessionStore(repo_path=repo_path)
        payload = store.load()
        return str(payload.get("selected_proposal_id", "")).strip()

    @staticmethod
    def _get_approval_mode(*, repo_path: str) -> str:
        store = RemoteSessionStore(repo_path=repo_path)
        payload = store.load()
        approval_mode = str(payload.get("approval_mode", "manual")).strip()
        if approval_mode not in {"manual", "auto"}:
            return "manual"
        return approval_mode

    @staticmethod
    def _get_stop_reservation(*, repo_path: str) -> bool:
        store = RemoteSessionStore(repo_path=repo_path)
        payload = store.load()
        return bool(payload.get("stop_after_current_task_requested", False))

    @staticmethod
    def _get_waiting_next_task_approval(*, repo_path: str) -> bool:
        store = RemoteSessionStore(repo_path=repo_path)
        payload = store.load()
        return bool(payload.get("waiting_next_task_approval", False))

    @staticmethod
    def _get_last_plan_director_decision(*, repo_path: str) -> str:
        store = RemoteSessionStore(repo_path=repo_path)
        payload = store.load()
        return str(payload.get("last_plan_director_decision", "")).strip()

    @staticmethod
    def _get_last_plan_director_selected_proposal_id(*, repo_path: str) -> str:
        store = RemoteSessionStore(repo_path=repo_path)
        payload = store.load()
        return str(payload.get("last_plan_director_selected_proposal_id", "")).strip()

    @staticmethod
    def _get_last_plan_director_selection_reason(*, repo_path: str) -> str:
        store = RemoteSessionStore(repo_path=repo_path)
        payload = store.load()
        return str(payload.get("last_plan_director_selection_reason", "")).strip()

    @staticmethod
    def _get_last_planner_role(*, repo_path: str) -> str:
        store = RemoteSessionStore(repo_path=repo_path)
        payload = store.load()
        planner_role = str(payload.get("last_planner_role", "planner_safe")).strip()
        if planner_role not in {"planner_safe", "planner_improvement"}:
            return "planner_safe"
        return planner_role
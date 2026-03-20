# src\claude_orchestrator\application\remote_operator\controller.py
from __future__ import annotations

from claude_orchestrator.application.remote_operator.constants import (
    DEFAULT_MENU,
    MENU_COMPLETED_TASK_LIST,
    MENU_CREATED_TASK,
    MENU_EXITED,
    MENU_IN_PROGRESS_TASK_LIST,
    MENU_MAIN,
    MENU_POST_RUN,
    MENU_PROPOSAL_LIST,
    MENU_SELECTED_PROPOSAL,
    MENU_SELECTED_TASK,
    MENU_TASK_LIST,
)
from claude_orchestrator.application.remote_operator.renderer import (
    RemoteOperatorRenderer,
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
                return self._generate_proposals_and_render(
                    repo_path=repo_path,
                    source_task_id=task_id,
                    previous_menu=MENU_MAIN,
                )
            return self._switch_menu(
                repo_path=repo_path,
                menu=MENU_COMPLETED_TASK_LIST,
                last_message="次タスク案を作成する completed task を選択してください。",
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

        return self._generate_proposals_and_render(
            repo_path=repo_path,
            source_task_id=str(selected["task_id"]),
            previous_menu=MENU_COMPLETED_TASK_LIST,
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
                return self._generate_proposals_and_render(
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
            store.update_fields(
                selected_task_id=source_task_id,
                current_menu=MENU_SELECTED_TASK,
                previous_menu=MENU_PROPOSAL_LIST,
                last_message=f"{source_task_id} の task 選択画面へ戻りました。",
            )
            return self._render_result(
                repo_path=repo_path,
                menu=MENU_SELECTED_TASK,
                last_message=f"{source_task_id} の task 選択画面へ戻りました。",
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
            if source_task_id:
                store.update_fields(
                    selected_task_id=source_task_id,
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
                return self._generate_proposals_and_render(
                    repo_path=repo_path,
                    source_task_id=task_id,
                    previous_menu=MENU_POST_RUN,
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

    def _generate_proposals_and_render(
        self,
        *,
        repo_path: str,
        source_task_id: str,
        previous_menu: str,
    ) -> dict:
        GenerateNextTaskProposalsUseCase().execute(
            repo_path=repo_path,
            source_task_id=source_task_id,
            reference_doc_paths=[],
        )

        store = RemoteSessionStore(repo_path=repo_path)
        store.update_fields(
            selected_task_id=source_task_id,
            selected_source_task_id=source_task_id,
            selected_proposal_id="",
            current_menu=MENU_PROPOSAL_LIST,
            previous_menu=previous_menu,
            last_message=f"{source_task_id} の次タスク案を作成しました。",
        )
        return self._render_result(
            repo_path=repo_path,
            menu=MENU_PROPOSAL_LIST,
            last_message=f"{source_task_id} の次タスク案を作成しました。",
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
                title="次タスク案を作成する completed task を選択してください",
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
            proposals = self._get_proposals(repo_path=repo_path, source_task_id=source_task_id)
            return self.renderer.render_proposal_list_menu(
                source_task_id=source_task_id,
                proposals=proposals,
                last_message=last_message,
            )

        if current_menu == MENU_SELECTED_PROPOSAL:
            source_task_id = self._get_selected_source_task_id(repo_path=repo_path)
            proposal_id = self._get_selected_proposal_id(repo_path=repo_path)
            proposal = self._find_proposal(
                proposals=self._get_proposals(repo_path=repo_path, source_task_id=source_task_id),
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
    def _get_selected_proposal_id(*, repo_path: str) -> str:
        store = RemoteSessionStore(repo_path=repo_path)
        payload = store.load()
        return str(payload.get("selected_proposal_id", "")).strip()
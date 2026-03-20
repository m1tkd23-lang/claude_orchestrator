# src\claude_orchestrator\application\usecases\remote_operator_usecase.py
from __future__ import annotations

from pathlib import Path

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


class RemoteOperatorUseCase:
    MENU_MAIN = "main"
    MENU_IN_PROGRESS_TASK_LIST = "in_progress_task_list"
    MENU_COMPLETED_TASK_LIST = "completed_task_list"
    MENU_TASK_LIST = "task_list"
    MENU_SELECTED_TASK = "selected_task"
    MENU_PROPOSAL_LIST = "proposal_list"
    MENU_SELECTED_PROPOSAL = "selected_proposal"
    MENU_CREATED_TASK = "created_task"
    MENU_POST_RUN = "post_run"
    MENU_EXITED = "exited"

    def show_menu(self, *, repo_path: str) -> dict:
        store = RemoteSessionStore(repo_path=repo_path)
        payload = store.load()

        current_menu = str(payload.get("current_menu", self.MENU_MAIN)).strip() or self.MENU_MAIN
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
        current_menu = str(payload.get("current_menu", self.MENU_MAIN)).strip() or self.MENU_MAIN

        if not normalized.isdigit():
            text = self._render_current_menu(
                repo_path=repo_path,
                current_menu=current_menu,
                last_message="無効な入力です。番号で入力してください。",
            )
            store.update_fields(last_message="無効な入力です。番号で入力してください。")
            return {
                "menu": current_menu,
                "text": text,
            }

        if current_menu == self.MENU_MAIN:
            return self._handle_main_menu(repo_path=repo_path, choice=normalized)

        if current_menu == self.MENU_IN_PROGRESS_TASK_LIST:
            return self._handle_in_progress_task_list(repo_path=repo_path, choice=normalized)

        if current_menu == self.MENU_COMPLETED_TASK_LIST:
            return self._handle_completed_task_list(repo_path=repo_path, choice=normalized)

        if current_menu == self.MENU_TASK_LIST:
            return self._handle_task_list(repo_path=repo_path, choice=normalized)

        if current_menu == self.MENU_SELECTED_TASK:
            return self._handle_selected_task(repo_path=repo_path, choice=normalized)

        if current_menu == self.MENU_PROPOSAL_LIST:
            return self._handle_proposal_list(repo_path=repo_path, choice=normalized)

        if current_menu == self.MENU_SELECTED_PROPOSAL:
            return self._handle_selected_proposal(repo_path=repo_path, choice=normalized)

        if current_menu == self.MENU_CREATED_TASK:
            return self._handle_created_task(repo_path=repo_path, choice=normalized)

        if current_menu == self.MENU_POST_RUN:
            return self._handle_post_run(repo_path=repo_path, choice=normalized)

        if current_menu == self.MENU_EXITED:
            return self._handle_exited(repo_path=repo_path, choice=normalized)

        store.reset_operator_state()
        text = self._render_current_menu(
            repo_path=repo_path,
            current_menu=self.MENU_MAIN,
            last_message="メニュー状態が不正だったため、メインメニューへ戻しました。",
        )
        return {
            "menu": self.MENU_MAIN,
            "text": text,
        }

    def _handle_main_menu(self, *, repo_path: str, choice: str) -> dict:
        store = RemoteSessionStore(repo_path=repo_path)

        if choice == "1":
            tasks = self._list_in_progress_tasks(repo_path=repo_path)
            if not tasks:
                return self._set_menu_and_render(
                    repo_path=repo_path,
                    menu=self.MENU_MAIN,
                    last_message="in_progress task はありません。",
                )
            if len(tasks) == 1:
                task_id = str(tasks[0]["task_id"])
                return self._run_task_and_render(repo_path=repo_path, task_id=task_id)

            return self._set_menu_and_render(
                repo_path=repo_path,
                menu=self.MENU_IN_PROGRESS_TASK_LIST,
                last_message="実行する in_progress task を選択してください。",
            )

        if choice == "2":
            tasks = self._list_completed_tasks(repo_path=repo_path)
            if not tasks:
                return self._set_menu_and_render(
                    repo_path=repo_path,
                    menu=self.MENU_MAIN,
                    last_message="completed task はありません。",
                )
            if len(tasks) == 1:
                task_id = str(tasks[0]["task_id"])
                return self._generate_proposals_and_render(
                    repo_path=repo_path,
                    source_task_id=task_id,
                )

            return self._set_menu_and_render(
                repo_path=repo_path,
                menu=self.MENU_COMPLETED_TASK_LIST,
                last_message="次タスク案を作成する completed task を選択してください。",
            )

        if choice == "3":
            return self._set_menu_and_render(
                repo_path=repo_path,
                menu=self.MENU_TASK_LIST,
                last_message="task 一覧です。番号で task を選択してください。0 で戻れます。",
            )

        if choice == "4":
            return self._set_menu_and_render(
                repo_path=repo_path,
                menu=self.MENU_TASK_LIST,
                last_message="選択する task を番号で指定してください。0 で戻れます。",
            )

        if choice == "5":
            store.update_fields(
                current_menu=self.MENU_EXITED,
                last_message="Remote Operator を終了状態にしました。",
            )
            return {
                "menu": self.MENU_EXITED,
                "text": self._render_current_menu(
                    repo_path=repo_path,
                    current_menu=self.MENU_EXITED,
                    last_message="Remote Operator を終了状態にしました。",
                ),
            }

        return self._set_menu_and_render(
            repo_path=repo_path,
            menu=self.MENU_MAIN,
            last_message="無効な入力です。番号で入力してください。",
        )

    def _handle_in_progress_task_list(self, *, repo_path: str, choice: str) -> dict:
        if choice == "0":
            return self._set_menu_and_render(
                repo_path=repo_path,
                menu=self.MENU_MAIN,
                last_message="メインメニューへ戻りました。",
            )

        tasks = self._list_in_progress_tasks(repo_path=repo_path)
        selected = self._select_from_numbered_items(tasks, choice)
        if selected is None:
            return self._set_menu_and_render(
                repo_path=repo_path,
                menu=self.MENU_IN_PROGRESS_TASK_LIST,
                last_message="無効な番号です。もう一度選択してください。",
            )

        return self._run_task_and_render(
            repo_path=repo_path,
            task_id=str(selected["task_id"]),
        )

    def _handle_completed_task_list(self, *, repo_path: str, choice: str) -> dict:
        if choice == "0":
            return self._set_menu_and_render(
                repo_path=repo_path,
                menu=self.MENU_MAIN,
                last_message="メインメニューへ戻りました。",
            )

        tasks = self._list_completed_tasks(repo_path=repo_path)
        selected = self._select_from_numbered_items(tasks, choice)
        if selected is None:
            return self._set_menu_and_render(
                repo_path=repo_path,
                menu=self.MENU_COMPLETED_TASK_LIST,
                last_message="無効な番号です。もう一度選択してください。",
            )

        return self._generate_proposals_and_render(
            repo_path=repo_path,
            source_task_id=str(selected["task_id"]),
        )

    def _handle_task_list(self, *, repo_path: str, choice: str) -> dict:
        if choice == "0":
            return self._set_menu_and_render(
                repo_path=repo_path,
                menu=self.MENU_MAIN,
                last_message="メインメニューへ戻りました。",
            )

        tasks = StatusUseCase().list_tasks(repo_path=repo_path)
        selected = self._select_from_numbered_items(tasks, choice)
        if selected is None:
            return self._set_menu_and_render(
                repo_path=repo_path,
                menu=self.MENU_TASK_LIST,
                last_message="無効な番号です。もう一度選択してください。",
            )

        task_id = str(selected["task_id"])
        store = RemoteSessionStore(repo_path=repo_path)
        store.update_fields(
            selected_task_id=task_id,
            selected_proposal_id="",
            current_menu=self.MENU_SELECTED_TASK,
            last_message=f"{task_id} を選択しました。",
        )

        return {
            "menu": self.MENU_SELECTED_TASK,
            "text": self._render_current_menu(
                repo_path=repo_path,
                current_menu=self.MENU_SELECTED_TASK,
                last_message=f"{task_id} を選択しました。",
            ),
        }

    def _handle_selected_task(self, *, repo_path: str, choice: str) -> dict:
        store = RemoteSessionStore(repo_path=repo_path)
        payload = store.load()
        task_id = str(payload.get("selected_task_id", "")).strip()
        if not task_id:
            return self._set_menu_and_render(
                repo_path=repo_path,
                menu=self.MENU_MAIN,
                last_message="選択中 task が無いため、メインメニューへ戻しました。",
            )

        task = StatusUseCase().get_task_status(repo_path=repo_path, task_id=task_id)
        status = str(task.get("status", "")).strip()

        if choice == "1":
            return {
                "menu": self.MENU_SELECTED_TASK,
                "text": self._render_current_menu(
                    repo_path=repo_path,
                    current_menu=self.MENU_SELECTED_TASK,
                    last_message=f"{task_id} の詳細を再表示します。",
                ),
            }

        if choice == "2":
            if status == "in_progress":
                return self._run_task_and_render(repo_path=repo_path, task_id=task_id)
            if status == "completed":
                return self._generate_proposals_and_render(
                    repo_path=repo_path,
                    source_task_id=task_id,
                )

            return self._set_menu_and_render(
                repo_path=repo_path,
                menu=self.MENU_SELECTED_TASK,
                last_message=(
                    f"{task_id} は status={status} のため、"
                    "この操作は実行できません。"
                ),
            )

        if choice == "9":
            return self._set_menu_and_render(
                repo_path=repo_path,
                menu=self.MENU_MAIN,
                last_message="メインメニューへ戻りました。",
            )

        return self._set_menu_and_render(
            repo_path=repo_path,
            menu=self.MENU_SELECTED_TASK,
            last_message="無効な番号です。もう一度選択してください。",
        )

    def _handle_proposal_list(self, *, repo_path: str, choice: str) -> dict:
        store = RemoteSessionStore(repo_path=repo_path)
        payload = store.load()
        source_task_id = str(payload.get("selected_task_id", "")).strip()
        if not source_task_id:
            return self._set_menu_and_render(
                repo_path=repo_path,
                menu=self.MENU_MAIN,
                last_message="source task が見つからないため、メインメニューへ戻しました。",
            )

        if choice == "0":
            store.update_fields(
                current_menu=self.MENU_SELECTED_TASK,
                selected_proposal_id="",
                last_message=f"{source_task_id} の task 選択画面へ戻りました。",
            )
            return {
                "menu": self.MENU_SELECTED_TASK,
                "text": self._render_current_menu(
                    repo_path=repo_path,
                    current_menu=self.MENU_SELECTED_TASK,
                    last_message=f"{source_task_id} の task 選択画面へ戻りました。",
                ),
            }

        result = ListProposalsUseCase().execute(
            repo_path=repo_path,
            source_task_id=source_task_id,
        )
        proposals = result["proposals"]
        selected = self._select_from_numbered_items(proposals, choice)
        if selected is None:
            return self._set_menu_and_render(
                repo_path=repo_path,
                menu=self.MENU_PROPOSAL_LIST,
                last_message="無効な番号です。もう一度選択してください。",
            )

        proposal_id = str(selected["proposal_id"]).strip()
        store.update_fields(
            current_menu=self.MENU_SELECTED_PROPOSAL,
            selected_proposal_id=proposal_id,
            last_message=f"{proposal_id} を選択しました。",
        )
        return {
            "menu": self.MENU_SELECTED_PROPOSAL,
            "text": self._render_current_menu(
                repo_path=repo_path,
                current_menu=self.MENU_SELECTED_PROPOSAL,
                last_message=f"{proposal_id} を選択しました。",
            ),
        }

    def _handle_selected_proposal(self, *, repo_path: str, choice: str) -> dict:
        store = RemoteSessionStore(repo_path=repo_path)
        payload = store.load()
        source_task_id = str(payload.get("selected_task_id", "")).strip()
        proposal_id = str(payload.get("selected_proposal_id", "")).strip()

        if not source_task_id or not proposal_id:
            return self._set_menu_and_render(
                repo_path=repo_path,
                menu=self.MENU_MAIN,
                last_message="proposal 選択状態が無いため、メインメニューへ戻しました。",
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
                selected_proposal_id="",
                current_menu=self.MENU_CREATED_TASK,
                last_message=(
                    f"{proposal_id} から {created_task_id} を作成しました。"
                ),
            )
            return {
                "menu": self.MENU_CREATED_TASK,
                "text": self._render_current_menu(
                    repo_path=repo_path,
                    current_menu=self.MENU_CREATED_TASK,
                    last_message=f"{proposal_id} から {created_task_id} を作成しました。",
                ),
            }

        if choice == "2":
            store.update_fields(
                current_menu=self.MENU_PROPOSAL_LIST,
                last_message=f"{source_task_id} の proposal 一覧へ戻りました。",
            )
            return {
                "menu": self.MENU_PROPOSAL_LIST,
                "text": self._render_current_menu(
                    repo_path=repo_path,
                    current_menu=self.MENU_PROPOSAL_LIST,
                    last_message=f"{source_task_id} の proposal 一覧へ戻りました。",
                ),
            }

        return self._set_menu_and_render(
            repo_path=repo_path,
            menu=self.MENU_SELECTED_PROPOSAL,
            last_message="無効な番号です。もう一度選択してください。",
        )

    def _handle_created_task(self, *, repo_path: str, choice: str) -> dict:
        store = RemoteSessionStore(repo_path=repo_path)
        payload = store.load()
        task_id = str(payload.get("selected_task_id", "")).strip()

        if not task_id:
            return self._set_menu_and_render(
                repo_path=repo_path,
                menu=self.MENU_MAIN,
                last_message="作成済み task が見つからないため、メインメニューへ戻しました。",
            )

        if choice == "1":
            return self._run_task_and_render(repo_path=repo_path, task_id=task_id)

        if choice == "2":
            return self._set_menu_and_render(
                repo_path=repo_path,
                menu=self.MENU_MAIN,
                last_message="メインメニューへ戻りました。",
            )

        return self._set_menu_and_render(
            repo_path=repo_path,
            menu=self.MENU_CREATED_TASK,
            last_message="無効な番号です。もう一度選択してください。",
        )

    def _handle_post_run(self, *, repo_path: str, choice: str) -> dict:
        store = RemoteSessionStore(repo_path=repo_path)
        payload = store.load()
        task_id = str(payload.get("selected_task_id", "")).strip()

        if not task_id:
            return self._set_menu_and_render(
                repo_path=repo_path,
                menu=self.MENU_MAIN,
                last_message="選択中 task が見つからないため、メインメニューへ戻しました。",
            )

        task = StatusUseCase().get_task_status(repo_path=repo_path, task_id=task_id)
        status = str(task.get("status", "")).strip()

        if status == "completed":
            if choice == "1":
                return self._generate_proposals_and_render(
                    repo_path=repo_path,
                    source_task_id=task_id,
                )
            if choice == "2":
                return self._set_menu_and_render(
                    repo_path=repo_path,
                    menu=self.MENU_TASK_LIST,
                    last_message="task 一覧へ移動しました。",
                )
            if choice == "3":
                return self._set_menu_and_render(
                    repo_path=repo_path,
                    menu=self.MENU_MAIN,
                    last_message="メインメニューへ戻りました。",
                )

            return self._set_menu_and_render(
                repo_path=repo_path,
                menu=self.MENU_POST_RUN,
                last_message="無効な番号です。もう一度選択してください。",
            )

        if choice == "1":
            return self._set_menu_and_render(
                repo_path=repo_path,
                menu=self.MENU_TASK_LIST,
                last_message="task 一覧へ移動しました。",
            )

        if choice == "2":
            return self._set_menu_and_render(
                repo_path=repo_path,
                menu=self.MENU_MAIN,
                last_message="メインメニューへ戻りました。",
            )

        return self._set_menu_and_render(
            repo_path=repo_path,
            menu=self.MENU_POST_RUN,
            last_message="無効な番号です。もう一度選択してください。",
        )

    def _handle_exited(self, *, repo_path: str, choice: str) -> dict:
        if choice == "1":
            return self._set_menu_and_render(
                repo_path=repo_path,
                menu=self.MENU_MAIN,
                last_message="メインメニューへ戻りました。",
            )

        return self._set_menu_and_render(
            repo_path=repo_path,
            menu=self.MENU_EXITED,
            last_message="終了状態です。1 を入力するとメインメニューへ戻ります。",
        )

    def _run_task_and_render(self, *, repo_path: str, task_id: str) -> dict:
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
            selected_proposal_id="",
            current_menu=self.MENU_POST_RUN,
            last_message=message,
        )

        return {
            "menu": self.MENU_POST_RUN,
            "text": self._render_current_menu(
                repo_path=repo_path,
                current_menu=self.MENU_POST_RUN,
                last_message=message,
            ),
        }

    def _generate_proposals_and_render(
        self,
        *,
        repo_path: str,
        source_task_id: str,
    ) -> dict:
        GenerateNextTaskProposalsUseCase().execute(
            repo_path=repo_path,
            source_task_id=source_task_id,
            reference_doc_paths=[],
        )

        store = RemoteSessionStore(repo_path=repo_path)
        store.update_fields(
            selected_task_id=source_task_id,
            selected_proposal_id="",
            current_menu=self.MENU_PROPOSAL_LIST,
            last_message=f"{source_task_id} の次タスク案を作成しました。",
        )

        return {
            "menu": self.MENU_PROPOSAL_LIST,
            "text": self._render_current_menu(
                repo_path=repo_path,
                current_menu=self.MENU_PROPOSAL_LIST,
                last_message=f"{source_task_id} の次タスク案を作成しました。",
            ),
        }

    def _set_menu_and_render(
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
        return {
            "menu": menu,
            "text": self._render_current_menu(
                repo_path=repo_path,
                current_menu=menu,
                last_message=last_message,
            ),
        }

    def _render_current_menu(
        self,
        *,
        repo_path: str,
        current_menu: str,
        last_message: str,
    ) -> str:
        if current_menu == self.MENU_MAIN:
            return self._render_main_menu(last_message=last_message)

        if current_menu == self.MENU_IN_PROGRESS_TASK_LIST:
            return self._render_task_list_menu(
                title="実行する in_progress task を選択してください",
                tasks=self._list_in_progress_tasks(repo_path=repo_path),
                last_message=last_message,
            )

        if current_menu == self.MENU_COMPLETED_TASK_LIST:
            return self._render_task_list_menu(
                title="次タスク案を作成する completed task を選択してください",
                tasks=self._list_completed_tasks(repo_path=repo_path),
                last_message=last_message,
            )

        if current_menu == self.MENU_TASK_LIST:
            return self._render_task_list_menu(
                title="task 一覧",
                tasks=StatusUseCase().list_tasks(repo_path=repo_path),
                last_message=last_message,
            )

        if current_menu == self.MENU_SELECTED_TASK:
            return self._render_selected_task_menu(
                repo_path=repo_path,
                last_message=last_message,
            )

        if current_menu == self.MENU_PROPOSAL_LIST:
            return self._render_proposal_list_menu(
                repo_path=repo_path,
                last_message=last_message,
            )

        if current_menu == self.MENU_SELECTED_PROPOSAL:
            return self._render_selected_proposal_menu(
                repo_path=repo_path,
                last_message=last_message,
            )

        if current_menu == self.MENU_CREATED_TASK:
            return self._render_created_task_menu(
                repo_path=repo_path,
                last_message=last_message,
            )

        if current_menu == self.MENU_POST_RUN:
            return self._render_post_run_menu(
                repo_path=repo_path,
                last_message=last_message,
            )

        if current_menu == self.MENU_EXITED:
            return self._render_exited_menu(last_message=last_message)

        return self._render_main_menu(
            last_message="メニュー状態が不正なため、メインメニューを表示します。"
        )

    def _render_main_menu(self, *, last_message: str) -> str:
        lines = []
        if last_message:
            lines.append(last_message)
            lines.append("")

        lines.extend(
            [
                "現在の操作候補です",
                "",
                "1. in_progress task を実行",
                "2. completed task から次タスク案を作成",
                "3. task 一覧を表示",
                "4. 特定 task を選択",
                "5. 終了",
                "",
                "番号で入力してください",
            ]
        )
        return "\n".join(lines)

    def _render_task_list_menu(
        self,
        *,
        title: str,
        tasks: list[dict],
        last_message: str,
    ) -> str:
        lines = []
        if last_message:
            lines.append(last_message)
            lines.append("")

        lines.append(title)
        lines.append("")

        if not tasks:
            lines.append("対象 task はありません。")
        else:
            for idx, task in enumerate(tasks, start=1):
                lines.append(
                    f"{idx}. {task['task_id']} | "
                    f"status={task['status']} | "
                    f"cycle={task['cycle']} | "
                    f"title={task['title']}"
                )

        lines.extend(
            [
                "",
                "0. 戻る",
                "",
                "番号で入力してください",
            ]
        )
        return "\n".join(lines)

    def _render_selected_task_menu(self, *, repo_path: str, last_message: str) -> str:
        store = RemoteSessionStore(repo_path=repo_path)
        payload = store.load()
        task_id = str(payload.get("selected_task_id", "")).strip()

        lines = []
        if last_message:
            lines.append(last_message)
            lines.append("")

        if not task_id:
            lines.extend(
                [
                    "選択中 task がありません。",
                    "",
                    "9. メインメニューへ戻る",
                    "",
                    "番号で入力してください",
                ]
            )
            return "\n".join(lines)

        task = StatusUseCase().get_task_status(repo_path=repo_path, task_id=task_id)
        status = str(task["status"]).strip()

        lines.extend(
            [
                f"選択中 task: {task_id}",
                f"title: {task['title']}",
                f"status: {status}",
                f"current: {task['current_stage']}",
                f"next_role: {task['next_role']}",
                f"cycle: {task['cycle']}",
                "",
                "1. task 詳細を再表示",
            ]
        )

        if status == "in_progress":
            lines.append("2. この task を実行")
        elif status == "completed":
            lines.append("2. この task から次タスク案を作成")
        else:
            lines.append("2. この task では利用できない操作")

        lines.extend(
            [
                "9. メインメニューへ戻る",
                "",
                "番号で入力してください",
            ]
        )
        return "\n".join(lines)

    def _render_proposal_list_menu(self, *, repo_path: str, last_message: str) -> str:
        store = RemoteSessionStore(repo_path=repo_path)
        payload = store.load()
        source_task_id = str(payload.get("selected_task_id", "")).strip()

        lines = []
        if last_message:
            lines.append(last_message)
            lines.append("")

        if not source_task_id:
            lines.extend(
                [
                    "source task がありません。",
                    "",
                    "0. 戻る",
                    "",
                    "番号で入力してください",
                ]
            )
            return "\n".join(lines)

        result = ListProposalsUseCase().execute(
            repo_path=repo_path,
            source_task_id=source_task_id,
        )

        lines.extend(
            [
                f"{source_task_id} の次タスク案",
                "",
            ]
        )

        proposals = result["proposals"]
        if not proposals:
            lines.append("proposal はありません。")
        else:
            for idx, proposal in enumerate(proposals, start=1):
                lines.append(
                    f"{idx}. {proposal['proposal_id']} | "
                    f"state={proposal['state']} | "
                    f"title={proposal['title']}"
                )

        lines.extend(
            [
                "",
                "0. 戻る",
                "",
                "番号で入力してください",
            ]
        )
        return "\n".join(lines)

    def _render_selected_proposal_menu(self, *, repo_path: str, last_message: str) -> str:
        store = RemoteSessionStore(repo_path=repo_path)
        payload = store.load()
        source_task_id = str(payload.get("selected_task_id", "")).strip()
        proposal_id = str(payload.get("selected_proposal_id", "")).strip()

        lines = []
        if last_message:
            lines.append(last_message)
            lines.append("")

        if not source_task_id or not proposal_id:
            lines.extend(
                [
                    "proposal が選択されていません。",
                    "",
                    "2. 戻る",
                    "",
                    "番号で入力してください",
                ]
            )
            return "\n".join(lines)

        result = ListProposalsUseCase().execute(
            repo_path=repo_path,
            source_task_id=source_task_id,
        )

        target = None
        for proposal in result["proposals"]:
            if str(proposal["proposal_id"]).strip() == proposal_id:
                target = proposal
                break

        if target is None:
            lines.extend(
                [
                    f"{proposal_id} が見つかりません。",
                    "",
                    "2. 戻る",
                    "",
                    "番号で入力してください",
                ]
            )
            return "\n".join(lines)

        depends_on = ", ".join(target["depends_on"]) if target["depends_on"] else "-"
        lines.extend(
            [
                f"選択中 proposal: {proposal_id}",
                f"title: {target['title']}",
                f"state: {target['state']}",
                f"why_now: {target['why_now'] or '-'}",
                f"depends_on: {depends_on}",
                f"description: {target['description'] or '-'}",
                "",
                "1. この proposal から task 作成",
                "2. 戻る",
                "",
                "番号で入力してください",
            ]
        )
        return "\n".join(lines)

    def _render_created_task_menu(self, *, repo_path: str, last_message: str) -> str:
        store = RemoteSessionStore(repo_path=repo_path)
        payload = store.load()
        created_task_id = str(payload.get("selected_task_id", "")).strip()

        lines = []
        if last_message:
            lines.append(last_message)
            lines.append("")

        lines.extend(
            [
                f"created_task_id: {created_task_id or '-'}",
                "",
                "1. そのまま実行",
                "2. メインメニューへ戻る",
                "",
                "番号で入力してください",
            ]
        )
        return "\n".join(lines)

    def _render_post_run_menu(self, *, repo_path: str, last_message: str) -> str:
        store = RemoteSessionStore(repo_path=repo_path)
        payload = store.load()
        task_id = str(payload.get("selected_task_id", "")).strip()

        lines = []
        if last_message:
            lines.append(last_message)
            lines.append("")

        if not task_id:
            lines.extend(
                [
                    "選択中 task がありません。",
                    "",
                    "2. メインメニューへ戻る",
                    "",
                    "番号で入力してください",
                ]
            )
            return "\n".join(lines)

        task = StatusUseCase().get_task_status(repo_path=repo_path, task_id=task_id)
        status = str(task["status"]).strip()

        if status == "completed":
            lines.extend(
                [
                    "次の操作を選んでください",
                    "",
                    "1. 次タスク案を作成する",
                    "2. task 一覧へ戻る",
                    "3. メインメニューへ戻る",
                    "",
                    "番号で入力してください",
                ]
            )
            return "\n".join(lines)

        lines.extend(
            [
                "次の操作を選んでください",
                "",
                "1. task 一覧へ戻る",
                "2. メインメニューへ戻る",
                "",
                "番号で入力してください",
            ]
        )
        return "\n".join(lines)

    def _render_exited_menu(self, *, last_message: str) -> str:
        lines = []
        if last_message:
            lines.append(last_message)
            lines.append("")

        lines.extend(
            [
                "Remote Operator は終了状態です。",
                "",
                "1. メインメニューへ戻る",
                "",
                "番号で入力してください",
            ]
        )
        return "\n".join(lines)

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
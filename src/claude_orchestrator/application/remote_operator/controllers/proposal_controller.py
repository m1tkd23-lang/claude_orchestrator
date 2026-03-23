# src\claude_orchestrator\application\remote_operator\controllers\proposal_controller.py
from __future__ import annotations

from claude_orchestrator.application.remote_operator.constants import (
    MENU_CREATED_TASK,
    MENU_MAIN,
    MENU_PROPOSAL_LIST,
    MENU_SELECTED_PROPOSAL,
    MENU_SELECTED_TASK,
)
from claude_orchestrator.application.usecases.create_task_from_proposal_usecase import (
    CreateTaskFromProposalUseCase,
)
from claude_orchestrator.application.usecases.list_proposals_usecase import (
    ListProposalsUseCase,
)
from claude_orchestrator.infrastructure.remote_session_store import RemoteSessionStore

from claude_orchestrator.application.remote_operator.controller_support import (
    RemoteOperatorControllerSupport,
)


class ProposalController:
    def __init__(self, support: RemoteOperatorControllerSupport) -> None:
        self.support = support

    def handle_list(self, *, repo_path: str, choice: str) -> dict:
        store = RemoteSessionStore(repo_path=repo_path)
        payload = store.load()
        source_task_id = str(payload.get("selected_source_task_id", "")).strip()
        if not source_task_id:
            source_task_id = str(payload.get("selected_task_id", "")).strip()

        if not source_task_id:
            return self.support.switch_menu(
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
            return self.support.render_result(
                repo_path=repo_path,
                menu=MENU_SELECTED_TASK,
                last_message=f"{source_task_id} の task 選択画面へ戻りました。",
            )

        planner_role = self.support.get_active_planner_role(repo_path=repo_path)
        result = ListProposalsUseCase().execute(
            repo_path=repo_path,
            source_task_id=source_task_id,
            planner_role=planner_role,
        )
        proposals = result["proposals"]
        selected = self.support.select_from_numbered_items(proposals, choice)
        if selected is None:
            return self.support.stay_with_message(
                repo_path=repo_path,
                menu=MENU_PROPOSAL_LIST,
                last_message="無効な番号です。もう一度選択してください。",
            )

        proposal_id = str(selected["proposal_id"]).strip()
        store.update_fields(
            selected_source_task_id=source_task_id,
            selected_proposal_id=proposal_id,
            selected_proposal_planner_role=planner_role,
            current_menu=MENU_SELECTED_PROPOSAL,
            previous_menu=MENU_PROPOSAL_LIST,
            last_message=f"{proposal_id} を選択しました。",
        )
        return self.support.render_result(
            repo_path=repo_path,
            menu=MENU_SELECTED_PROPOSAL,
            last_message=f"{proposal_id} を選択しました。",
        )

    def handle_selected(self, *, repo_path: str, choice: str) -> dict:
        store = RemoteSessionStore(repo_path=repo_path)
        payload = store.load()
        source_task_id = str(payload.get("selected_source_task_id", "")).strip()
        proposal_id = str(payload.get("selected_proposal_id", "")).strip()
        proposal_planner_role = self.support.get_selected_proposal_planner_role(repo_path=repo_path)

        if not source_task_id or not proposal_id:
            return self.support.switch_menu(
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
                planner_role=proposal_planner_role,
            )
            created_task_id = str(result["created_task_id"]).strip()
            store.update_fields(
                selected_task_id=created_task_id,
                selected_source_task_id=source_task_id,
                selected_proposal_id=proposal_id,
                selected_proposal_planner_role=proposal_planner_role,
                current_menu=MENU_CREATED_TASK,
                previous_menu=MENU_SELECTED_PROPOSAL,
                last_message=(
                    f"{proposal_id} ({proposal_planner_role}) から "
                    f"{created_task_id} を作成しました。"
                ),
            )
            return self.support.render_result(
                repo_path=repo_path,
                menu=MENU_CREATED_TASK,
                last_message=(
                    f"{proposal_id} ({proposal_planner_role}) から "
                    f"{created_task_id} を作成しました。"
                ),
            )

        if choice == "0":
            store.update_fields(
                current_menu=MENU_PROPOSAL_LIST,
                previous_menu=MENU_SELECTED_PROPOSAL,
                last_message=f"{source_task_id} の proposal 一覧へ戻りました。",
            )
            return self.support.render_result(
                repo_path=repo_path,
                menu=MENU_PROPOSAL_LIST,
                last_message=f"{source_task_id} の proposal 一覧へ戻りました。",
            )

        return self.support.stay_with_message(
            repo_path=repo_path,
            menu=MENU_SELECTED_PROPOSAL,
            last_message="無効な番号です。もう一度選択してください。",
        )
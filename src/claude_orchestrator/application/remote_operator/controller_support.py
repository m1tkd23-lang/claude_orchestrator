# src\claude_orchestrator\application\remote_operator\controller_support.py
from __future__ import annotations

import json
from pathlib import Path

from claude_orchestrator.application.remote_operator.constants import (
    DEFAULT_MENU,
    DEFAULT_PLANNER_ROLE,
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
    PLANNER_ROLES,
)
from claude_orchestrator.application.remote_operator.renderer import (
    RemoteOperatorRenderer,
)
from claude_orchestrator.application.usecases.approve_next_task_usecase import (
    ApproveNextTaskUseCase,
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
from claude_orchestrator.application.usecases.prepare_next_task_approval_usecase import (
    PrepareNextTaskApprovalUseCase,
)
from claude_orchestrator.application.usecases.reject_next_task_usecase import (
    RejectNextTaskUseCase,
)
from claude_orchestrator.application.usecases.run_plan_director_usecase import (
    RunPlanDirectorUseCase,
)
from claude_orchestrator.application.usecases.run_task_usecase import (
    RunTaskUseCase,
)
from claude_orchestrator.application.usecases.status_usecase import StatusUseCase
from claude_orchestrator.infrastructure.next_task_approval_store import (
    NextTaskApprovalStore,
)
from claude_orchestrator.infrastructure.project_paths import ProjectPaths
from claude_orchestrator.infrastructure.remote_session_store import RemoteSessionStore


class RemoteOperatorControllerSupport:
    _SUPPORTED_DEVELOPMENT_MODES = {
        "mainline",
        "maintenance",
    }
    _DEFAULT_DEVELOPMENT_MODE = "maintenance"

    def __init__(self) -> None:
        self.renderer = RemoteOperatorRenderer()

    def render_current_menu(
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
                tasks=self.list_in_progress_tasks(repo_path=repo_path),
                last_message=last_message,
            )

        if current_menu == MENU_COMPLETED_TASK_LIST:
            return self.renderer.render_task_list_menu(
                title="次タスク案を作成する completed task を選択してください",
                tasks=self.list_completed_tasks(repo_path=repo_path),
                last_message=last_message,
            )

        if current_menu == MENU_TASK_LIST:
            return self.renderer.render_task_list_menu(
                title="task 一覧",
                tasks=StatusUseCase().list_tasks(repo_path=repo_path),
                last_message=last_message,
            )

        if current_menu == MENU_SELECTED_TASK:
            task = self.get_selected_task(repo_path=repo_path)
            return self.renderer.render_selected_task_menu(
                task=task,
                last_message=last_message,
            )

        if current_menu == MENU_PROPOSAL_LIST:
            source_task_id = self.get_selected_source_task_id(repo_path=repo_path)
            planner_role = self.get_active_planner_role(repo_path=repo_path)
            proposals = self.get_proposals(
                repo_path=repo_path,
                source_task_id=source_task_id,
                planner_role=planner_role,
            )
            return self.renderer.render_proposal_list_menu(
                source_task_id=source_task_id,
                planner_role=planner_role,
                proposals=proposals,
                last_message=last_message,
            )

        if current_menu == MENU_SELECTED_PROPOSAL:
            source_task_id = self.get_selected_source_task_id(repo_path=repo_path)
            proposal_id = self.get_selected_proposal_id(repo_path=repo_path)
            proposal_planner_role = self.get_selected_proposal_planner_role(repo_path=repo_path)
            proposal = self.find_proposal(
                proposals=self.get_proposals(
                    repo_path=repo_path,
                    source_task_id=source_task_id,
                    planner_role=proposal_planner_role,
                ),
                proposal_id=proposal_id,
            )
            return self.renderer.render_selected_proposal_menu(
                proposal_id=proposal_id,
                planner_role=proposal_planner_role,
                proposal=proposal,
                last_message=last_message,
            )

        if current_menu == MENU_CREATED_TASK:
            created_task_id = self.get_selected_task_id(repo_path=repo_path)
            return self.renderer.render_created_task_menu(
                created_task_id=created_task_id,
                last_message=last_message,
            )

        if current_menu == MENU_POST_RUN:
            task_id = self.get_selected_task_id(repo_path=repo_path)
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
            source_task_id = self.get_post_pipeline_source_task_id(repo_path=repo_path)
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
                approval_mode=self.get_approval_mode(repo_path=repo_path),
                stop_after_current_task_requested=self.get_stop_reservation(
                    repo_path=repo_path
                ),
                active_planner_role=self.get_active_planner_role(repo_path=repo_path),
                last_planner_role=self.get_last_planner_role(repo_path=repo_path),
                last_plan_director_decision=self.get_last_plan_director_decision(
                    repo_path=repo_path
                ),
                waiting_next_task_approval=self.get_waiting_next_task_approval(
                    repo_path=repo_path
                ),
                development_mode=self.get_development_mode(repo_path=repo_path),
                last_message=last_message,
            )

        if current_menu == MENU_PLAN_DIRECTOR_RESULT:
            return self.renderer.render_plan_director_result_menu(
                source_task_id=self.get_post_pipeline_source_task_id(repo_path=repo_path),
                decision=self.get_last_plan_director_decision(repo_path=repo_path),
                selected_proposal_id=self.get_last_plan_director_selected_proposal_id(
                    repo_path=repo_path
                ),
                selected_planner_role=self.get_last_planner_role(repo_path=repo_path),
                selection_reason=self.get_last_plan_director_selection_reason(
                    repo_path=repo_path
                ),
                approval_mode=self.get_approval_mode(repo_path=repo_path),
                waiting_next_task_approval=self.get_waiting_next_task_approval(
                    repo_path=repo_path
                ),
                last_message=last_message,
            )

        if current_menu == MENU_NEXT_TASK_APPROVAL:
            return self.renderer.render_next_task_approval_menu(
                source_task_id=self.get_post_pipeline_source_task_id(repo_path=repo_path),
                decision=self.get_last_plan_director_decision(repo_path=repo_path),
                selected_proposal_id=self.get_last_plan_director_selected_proposal_id(
                    repo_path=repo_path
                ),
                selected_planner_role=self.get_last_planner_role(repo_path=repo_path),
                selection_reason=self.get_last_plan_director_selection_reason(
                    repo_path=repo_path
                ),
                last_message=last_message,
            )

        if current_menu == MENU_PIPELINE_SETTINGS:
            return self.renderer.render_pipeline_settings_menu(
                active_planner_role=self.get_active_planner_role(repo_path=repo_path),
                approval_mode=self.get_approval_mode(repo_path=repo_path),
                stop_after_current_task_requested=self.get_stop_reservation(
                    repo_path=repo_path
                ),
                development_mode=self.get_development_mode(repo_path=repo_path),
                last_message=last_message,
            )

        if current_menu == MENU_EXITED:
            return self.renderer.render_exited_menu(last_message=last_message)

        return self.renderer.render_main_menu(
            last_message="メニュー状態が不正なため、メインメニューを表示します。"
        )

    def render_result(
        self,
        *,
        repo_path: str,
        menu: str,
        last_message: str,
    ) -> dict:
        text = self.render_current_menu(
            repo_path=repo_path,
            current_menu=menu,
            last_message=last_message,
        )
        return {
            "menu": menu,
            "text": text,
        }

    def switch_menu(
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
        return self.render_result(
            repo_path=repo_path,
            menu=menu,
            last_message=last_message,
        )

    def stay_with_message(
        self,
        *,
        repo_path: str,
        menu: str,
        last_message: str,
    ) -> dict:
        store = RemoteSessionStore(repo_path=repo_path)
        payload = store.load()
        previous_menu = str(payload.get("previous_menu", DEFAULT_MENU)).strip() or DEFAULT_MENU
        store.update_fields(
            current_menu=menu,
            previous_menu=previous_menu,
            last_message=last_message,
        )
        return self.render_result(
            repo_path=repo_path,
            menu=menu,
            last_message=last_message,
        )

    def enter_post_pipeline(
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
            selected_proposal_id="",
            selected_proposal_planner_role="",
            post_run_source_task_id=source_task_id,
            current_menu=MENU_POST_PIPELINE,
            previous_menu=previous_menu,
            last_message=last_message,
        )
        return self.render_result(
            repo_path=repo_path,
            menu=MENU_POST_PIPELINE,
            last_message=last_message,
        )

    def run_task_and_render(
        self,
        *,
        repo_path: str,
        task_id: str,
        previous_menu: str,
    ) -> dict:
        store = RemoteSessionStore(repo_path=repo_path)
        payload = store.load()
        session_name = str(payload.get("session_name", "")).strip() or "unknown"

        result = RunTaskUseCase().execute(
            repo_path=repo_path,
            task_id=task_id,
            executor_type="remote",
            executor_id=f"remote:{session_name}",
            executor_label=f"Remote({session_name})",
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

        store.update_fields(
            selected_task_id=task_id,
            current_menu=MENU_POST_RUN,
            previous_menu=previous_menu,
            last_message=message,
        )
        return self.render_result(
            repo_path=repo_path,
            menu=MENU_POST_RUN,
            last_message=message,
        )

    def run_standard_task_pipeline_and_render(
        self,
        *,
        repo_path: str,
        task_id: str,
        previous_menu: str,
    ) -> dict:
        store = RemoteSessionStore(repo_path=repo_path)
        payload = store.load()
        session_name = str(payload.get("session_name", "")).strip() or "unknown"

        run_result = RunTaskUseCase().execute(
            repo_path=repo_path,
            task_id=task_id,
            executor_type="remote",
            executor_id=f"remote:{session_name}",
            executor_label=f"Remote({session_name})",
        )
        status = str(run_result.get("status", "")).strip()

        if status == "completed":
            return self.enter_post_pipeline(
                repo_path=repo_path,
                source_task_id=task_id,
                previous_menu=previous_menu,
                last_message=f"{task_id} を標準ライン自動実行し、completed になりました。",
            )

        return self.render_result(
            repo_path=repo_path,
            menu=MENU_POST_RUN,
            last_message=(
                f"{task_id} の標準ライン自動実行を完了しましたが、"
                f"status={status or '-'} のため後工程には進みません。"
            ),
        )

    def generate_proposals_and_render(
        self,
        *,
        repo_path: str,
        source_task_id: str,
        previous_menu: str,
        planner_role: str | None = None,
    ) -> dict:
        normalized_planner_role = planner_role or self.get_active_planner_role(repo_path=repo_path)
        GenerateNextTaskProposalsUseCase().execute(
            repo_path=repo_path,
            source_task_id=source_task_id,
            reference_doc_paths=[],
            planner_role=normalized_planner_role,
        )
        store = RemoteSessionStore(repo_path=repo_path)
        store.update_fields(
            selected_task_id=source_task_id,
            selected_source_task_id=source_task_id,
            selected_proposal_id="",
            selected_proposal_planner_role="",
            current_menu=MENU_PROPOSAL_LIST,
            previous_menu=previous_menu,
            active_planner_role=normalized_planner_role,
            last_planner_role=normalized_planner_role,
            waiting_next_task_approval=False,
            last_plan_director_decision="",
            last_plan_director_selected_proposal_id="",
            last_plan_director_selection_reason="",
            last_message=(
                f"{source_task_id} の planner ({normalized_planner_role}) を実行し、"
                "次タスク案を作成しました。"
            ),
        )
        return self.render_result(
            repo_path=repo_path,
            menu=MENU_PROPOSAL_LIST,
            last_message=(
                f"{source_task_id} の planner ({normalized_planner_role}) を実行し、"
                "次タスク案を作成しました。"
            ),
        )

    def run_plan_director_and_render(
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
        ).strip() or self.get_active_planner_role(repo_path=repo_path)

        approval_mode = self.get_approval_mode(repo_path=repo_path)
        waiting_next_task_approval = decision == "adopt" and approval_mode == "manual"

        if waiting_next_task_approval:
            session_name = self.get_session_name(repo_path=repo_path)
            PrepareNextTaskApprovalUseCase().execute(
                repo_path=repo_path,
                source_task_id=source_task_id,
                cycle=int(result.get("cycle", 0)),
                decision=decision,
                selected_proposal_id=selected_proposal_id,
                selected_planner_role=selected_planner_role,
                selection_reason=selection_reason,
                executor_type="remote",
                executor_id=f"remote:{session_name}",
                executor_label=f"Remote({session_name})",
            )
            next_menu = MENU_NEXT_TASK_APPROVAL
        else:
            NextTaskApprovalStore(
                repo_path=repo_path,
                source_task_id=source_task_id,
            ).clear()
            next_menu = MENU_PLAN_DIRECTOR_RESULT

        message = (
            f"{source_task_id} の plan_director を実行しました。"
            f" decision={decision or '-'}"
        )

        store = RemoteSessionStore(repo_path=repo_path)
        store.update_fields(
            selected_task_id=source_task_id,
            selected_source_task_id=source_task_id,
            selected_proposal_id="",
            selected_proposal_planner_role="",
            post_run_source_task_id=source_task_id,
            active_planner_role=selected_planner_role,
            last_plan_director_decision=decision,
            last_plan_director_selected_proposal_id=selected_proposal_id,
            last_plan_director_selection_reason=selection_reason,
            last_planner_role=selected_planner_role,
            waiting_next_task_approval=waiting_next_task_approval,
            current_menu=next_menu,
            previous_menu=previous_menu,
            last_message=message,
        )

        if decision == "adopt" and approval_mode == "auto":
            return self.create_task_from_plan_director_and_render(
                repo_path=repo_path,
                source_task_id=source_task_id,
                previous_menu=previous_menu,
                message_prefix=message,
            )

        return self.render_result(
            repo_path=repo_path,
            menu=next_menu,
            last_message=message,
        )

    def run_post_pipeline_auto_and_render(
        self,
        *,
        repo_path: str,
        source_task_id: str,
        previous_menu: str,
        preface_message: str = "",
    ) -> dict:
        planner_role = self.get_active_planner_role(repo_path=repo_path)

        GenerateNextTaskProposalsUseCase().execute(
            repo_path=repo_path,
            source_task_id=source_task_id,
            reference_doc_paths=[],
            planner_role=planner_role,
        )
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
        ).strip() or planner_role
        approval_mode = self.get_approval_mode(repo_path=repo_path)

        waiting_next_task_approval = decision == "adopt" and approval_mode == "manual"
        auto_message = (
            f"{source_task_id} の planner ({planner_role}) → "
            f"plan_director を自動実行しました。 decision={decision or '-'}"
        )
        final_message = auto_message if not preface_message else f"{preface_message}\n\n{auto_message}"

        if waiting_next_task_approval:
            session_name = self.get_session_name(repo_path=repo_path)
            PrepareNextTaskApprovalUseCase().execute(
                repo_path=repo_path,
                source_task_id=source_task_id,
                cycle=int(result.get("cycle", 0)),
                decision=decision,
                selected_proposal_id=selected_proposal_id,
                selected_planner_role=selected_planner_role,
                selection_reason=selection_reason,
                executor_type="remote",
                executor_id=f"remote:{session_name}",
                executor_label=f"Remote({session_name})",
            )
        else:
            NextTaskApprovalStore(
                repo_path=repo_path,
                source_task_id=source_task_id,
            ).clear()

        store = RemoteSessionStore(repo_path=repo_path)
        store.update_fields(
            selected_task_id=source_task_id,
            selected_source_task_id=source_task_id,
            selected_proposal_id="",
            selected_proposal_planner_role="",
            post_run_source_task_id=source_task_id,
            active_planner_role=planner_role,
            last_plan_director_decision=decision,
            last_plan_director_selected_proposal_id=selected_proposal_id,
            last_plan_director_selection_reason=selection_reason,
            last_planner_role=selected_planner_role,
            waiting_next_task_approval=waiting_next_task_approval,
            last_message=final_message,
        )

        if decision == "adopt" and approval_mode == "auto":
            return self.create_task_from_plan_director_and_render(
                repo_path=repo_path,
                source_task_id=source_task_id,
                previous_menu=previous_menu,
                message_prefix=final_message,
            )

        next_menu = MENU_PLAN_DIRECTOR_RESULT
        if waiting_next_task_approval:
            next_menu = MENU_NEXT_TASK_APPROVAL

        store.update_fields(
            current_menu=next_menu,
            previous_menu=previous_menu,
        )
        return self.render_result(
            repo_path=repo_path,
            menu=next_menu,
            last_message=final_message,
        )

    def create_task_from_plan_director_and_render(
        self,
        *,
        repo_path: str,
        source_task_id: str,
        previous_menu: str,
        message_prefix: str = "",
    ) -> dict:
        session_name = self.get_session_name(repo_path=repo_path)
        result = ApproveNextTaskUseCase().execute(
            repo_path=repo_path,
            source_task_id=source_task_id,
            executor_type="remote",
            executor_id=f"remote:{session_name}",
            executor_label=f"Remote({session_name})",
        )
        created_task_id = str(result.get("created_task_id") or "").strip()

        if not bool(result.get("approved")) or not created_task_id:
            message = str(result.get("message", "")).strip() or "次 task は作成されませんでした。"
            if message_prefix:
                message = f"{message_prefix}\n\n{message}"
            return self.enter_post_pipeline(
                repo_path=repo_path,
                source_task_id=source_task_id,
                previous_menu=previous_menu,
                last_message=message,
            )

        selected_planner_role = str(result.get("selected_planner_role", "")).strip()
        message = (
            f"{source_task_id} から {created_task_id} を作成しました。"
            f" planner_role={selected_planner_role or '-'}"
        )
        if message_prefix:
            message = f"{message_prefix}\n\n{message}"

        store = RemoteSessionStore(repo_path=repo_path)
        store.update_fields(
            selected_task_id=created_task_id,
            selected_source_task_id=source_task_id,
            current_menu=MENU_CREATED_TASK,
            previous_menu=previous_menu,
            waiting_next_task_approval=False,
            active_planner_role=selected_planner_role or self.get_active_planner_role(repo_path=repo_path),
            selected_proposal_planner_role=selected_planner_role or "",
            last_message=message,
        )
        return self.render_result(
            repo_path=repo_path,
            menu=MENU_CREATED_TASK,
            last_message=message,
        )

    @staticmethod
    def list_in_progress_tasks(*, repo_path: str) -> list[dict]:
        tasks = StatusUseCase().list_tasks(repo_path=repo_path)
        return [task for task in tasks if str(task.get("status")) == "in_progress"]

    @staticmethod
    def list_completed_tasks(*, repo_path: str) -> list[dict]:
        tasks = StatusUseCase().list_tasks(repo_path=repo_path)
        return [task for task in tasks if str(task.get("status")) == "completed"]

    @staticmethod
    def select_from_numbered_items(items: list[dict], choice: str) -> dict | None:
        if not choice.isdigit():
            return None
        index = int(choice)
        if index <= 0 or index > len(items):
            return None
        return items[index - 1]

    @staticmethod
    def find_proposal(*, proposals: list[dict], proposal_id: str) -> dict | None:
        normalized = str(proposal_id).strip()
        for proposal in proposals:
            if str(proposal.get("proposal_id", "")).strip() == normalized:
                return proposal
        return None

    @staticmethod
    def get_proposals(
        *,
        repo_path: str,
        source_task_id: str,
        planner_role: str,
    ) -> list[dict]:
        if not source_task_id:
            return []
        result = ListProposalsUseCase().execute(
            repo_path=repo_path,
            source_task_id=source_task_id,
            planner_role=planner_role,
        )
        return list(result.get("proposals", []) or [])

    @staticmethod
    def get_selected_task(repo_path: str) -> dict | None:
        task_id = RemoteOperatorControllerSupport.get_selected_task_id(repo_path=repo_path)
        if not task_id:
            return None
        return StatusUseCase().get_task_status(repo_path=repo_path, task_id=task_id)

    @staticmethod
    def get_selected_task_id(*, repo_path: str) -> str:
        store = RemoteSessionStore(repo_path=repo_path)
        payload = store.load()
        return str(payload.get("selected_task_id", "")).strip()

    @staticmethod
    def get_selected_source_task_id(*, repo_path: str) -> str:
        store = RemoteSessionStore(repo_path=repo_path)
        payload = store.load()
        source_task_id = str(payload.get("selected_source_task_id", "")).strip()
        if source_task_id:
            return source_task_id
        return str(payload.get("selected_task_id", "")).strip()

    @staticmethod
    def get_post_pipeline_source_task_id(*, repo_path: str) -> str:
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
    def get_selected_proposal_id(*, repo_path: str) -> str:
        store = RemoteSessionStore(repo_path=repo_path)
        payload = store.load()
        return str(payload.get("selected_proposal_id", "")).strip()

    @staticmethod
    def get_approval_mode(*, repo_path: str) -> str:
        store = RemoteSessionStore(repo_path=repo_path)
        payload = store.load()
        approval_mode = str(payload.get("approval_mode", "manual")).strip()
        if approval_mode not in {"manual", "auto"}:
            return "manual"
        return approval_mode

    @staticmethod
    def get_stop_reservation(*, repo_path: str) -> bool:
        store = RemoteSessionStore(repo_path=repo_path)
        payload = store.load()
        return bool(payload.get("stop_after_current_task_requested", False))

    @staticmethod
    def get_waiting_next_task_approval(*, repo_path: str) -> bool:
        source_task_id = RemoteOperatorControllerSupport.get_post_pipeline_source_task_id(
            repo_path=repo_path
        )
        if source_task_id:
            pending_store = NextTaskApprovalStore(
                repo_path=repo_path,
                source_task_id=source_task_id,
            )
            if pending_store.is_waiting():
                return True

        store = RemoteSessionStore(repo_path=repo_path)
        payload = store.load()
        return bool(payload.get("waiting_next_task_approval", False))

    @staticmethod
    def get_last_plan_director_decision(*, repo_path: str) -> str:
        store = RemoteSessionStore(repo_path=repo_path)
        payload = store.load()
        return str(payload.get("last_plan_director_decision", "")).strip()

    @staticmethod
    def get_last_plan_director_selected_proposal_id(*, repo_path: str) -> str:
        store = RemoteSessionStore(repo_path=repo_path)
        payload = store.load()
        return str(payload.get("last_plan_director_selected_proposal_id", "")).strip()

    @staticmethod
    def get_last_plan_director_selection_reason(*, repo_path: str) -> str:
        store = RemoteSessionStore(repo_path=repo_path)
        payload = store.load()
        return str(payload.get("last_plan_director_selection_reason", "")).strip()

    @staticmethod
    def get_last_planner_role(*, repo_path: str) -> str:
        store = RemoteSessionStore(repo_path=repo_path)
        payload = store.load()
        planner_role = str(payload.get("last_planner_role", DEFAULT_PLANNER_ROLE)).strip()
        if planner_role not in PLANNER_ROLES:
            return DEFAULT_PLANNER_ROLE
        return planner_role

    @staticmethod
    def get_active_planner_role(*, repo_path: str) -> str:
        store = RemoteSessionStore(repo_path=repo_path)
        payload = store.load()
        planner_role = str(payload.get("active_planner_role", DEFAULT_PLANNER_ROLE)).strip()
        if planner_role not in PLANNER_ROLES:
            return DEFAULT_PLANNER_ROLE
        return planner_role

    @staticmethod
    def get_selected_proposal_planner_role(*, repo_path: str) -> str:
        store = RemoteSessionStore(repo_path=repo_path)
        payload = store.load()
        planner_role = str(payload.get("selected_proposal_planner_role", "")).strip()
        if planner_role in PLANNER_ROLES:
            return planner_role
        return RemoteOperatorControllerSupport.get_active_planner_role(repo_path=repo_path)

    @staticmethod
    def get_session_name(*, repo_path: str) -> str:
        store = RemoteSessionStore(repo_path=repo_path)
        payload = store.load()
        return str(payload.get("session_name", "")).strip() or "unknown"

    def get_development_mode(self, *, repo_path: str) -> str:
        project_paths = ProjectPaths(target_repo=Path(repo_path))
        config = project_paths.load_project_config()
        raw_value = str(
            config.get("development_mode", self._DEFAULT_DEVELOPMENT_MODE)
        ).strip()
        if raw_value in self._SUPPORTED_DEVELOPMENT_MODES:
            return raw_value
        return self._DEFAULT_DEVELOPMENT_MODE

    def set_development_mode(self, *, repo_path: str, development_mode: str) -> None:
        normalized = self.normalize_development_mode(development_mode)

        project_paths = ProjectPaths(target_repo=Path(repo_path))
        project_paths.ensure_initialized()

        config_path = project_paths.project_config_path
        with config_path.open("r", encoding="utf-8") as file:
            payload = json.load(file)

        payload["development_mode"] = normalized

        with config_path.open("w", encoding="utf-8") as file:
            json.dump(payload, file, ensure_ascii=False, indent=2)
            file.write("\n")

    def normalize_development_mode(self, value: str) -> str:
        normalized = str(value).strip()
        if normalized in self._SUPPORTED_DEVELOPMENT_MODES:
            return normalized
        return self._DEFAULT_DEVELOPMENT_MODE
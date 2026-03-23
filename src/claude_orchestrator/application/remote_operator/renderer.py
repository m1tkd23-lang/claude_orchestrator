# src\claude_orchestrator\application\remote_operator\renderer.py
from __future__ import annotations


class RemoteOperatorRenderer:
    def render_main_menu(self, *, last_message: str) -> str:
        lines = self._start_lines(last_message)
        lines.extend(
            [
                "現在の操作候補です",
                "",
                "[1] in_progress task を実行",
                "[2] completed task の後工程を操作",
                "[3] task 一覧を表示",
                "[4] 特定 task を選択",
                "[5] 終了",
                "",
                "番号で入力してください",
            ]
        )
        return "\n".join(lines)

    def render_task_list_menu(
        self,
        *,
        title: str,
        tasks: list[dict],
        last_message: str,
    ) -> str:
        lines = self._start_lines(last_message, title=title)
        lines.append(title)
        lines.append("")

        if not tasks:
            lines.append("対象 task はありません。")
        else:
            for idx, task in enumerate(tasks, start=1):
                lines.append(
                    f"[{idx}] {task['task_id']} | "
                    f"status={task['status']} | "
                    f"cycle={task['cycle']} | "
                    f"title={task['title']}"
                )

        lines.extend(
            [
                "",
                "[0] 戻る",
                "",
                "番号で入力してください",
            ]
        )
        return "\n".join(lines)

    def render_selected_task_menu(
        self,
        *,
        task: dict | None,
        last_message: str,
    ) -> str:
        lines = self._start_lines(last_message)

        if task is None:
            lines.extend(
                [
                    "選択中 task がありません。",
                    "",
                    "[0] 戻る",
                    "",
                    "番号で入力してください",
                ]
            )
            return "\n".join(lines)

        status = str(task["status"]).strip()
        lines.extend(
            [
                f"選択中 task: {task['task_id']}",
                f"title: {task['title']}",
                f"status: {status}",
                f"current: {task['current_stage']}",
                f"next_role: {task['next_role']}",
                f"cycle: {task['cycle']}",
                "",
                "[1] task 詳細を再表示",
            ]
        )

        if status == "in_progress":
            lines.extend(
                [
                    "[2] この task を実行",
                    "[3] この task を標準ライン自動実行",
                ]
            )
        elif status == "completed":
            lines.extend(
                [
                    "[2] この task の後工程メニューへ移動",
                    "[3] planner → plan_director を自動実行",
                ]
            )
        else:
            lines.append("[2] この task では利用できない操作")

        lines.extend(
            [
                "[0] 戻る",
                "",
                "番号で入力してください",
            ]
        )
        return "\n".join(lines)

    def render_proposal_list_menu(
        self,
        *,
        source_task_id: str,
        planner_role: str,
        proposals: list[dict],
        last_message: str,
    ) -> str:
        title = f"{source_task_id} の次タスク案" if source_task_id else "次タスク案"
        lines = self._start_lines(last_message, title=title)

        if not source_task_id:
            lines.extend(
                [
                    "source task がありません。",
                    "",
                    "[0] 戻る",
                    "",
                    "番号で入力してください",
                ]
            )
            return "\n".join(lines)

        lines.extend(
            [
                title,
                f"planner_role: {planner_role or '-'}",
                "",
            ]
        )

        if not proposals:
            lines.append("proposal はありません。")
        else:
            for idx, proposal in enumerate(proposals, start=1):
                lines.append(
                    f"[{idx}] {proposal['proposal_id']} | "
                    f"state={proposal['state']} | "
                    f"title={proposal['title']}"
                )

        lines.extend(
            [
                "",
                "[0] 戻る",
                "",
                "番号で入力してください",
            ]
        )
        return "\n".join(lines)

    def render_selected_proposal_menu(
        self,
        *,
        proposal_id: str,
        planner_role: str,
        proposal: dict | None,
        last_message: str,
    ) -> str:
        lines = self._start_lines(last_message)

        if proposal is None:
            lines.extend(
                [
                    f"{proposal_id or 'proposal'} が見つかりません。",
                    f"planner_role: {planner_role or '-'}",
                    "",
                    "[0] 戻る",
                    "",
                    "番号で入力してください",
                ]
            )
            return "\n".join(lines)

        depends_on = ", ".join(proposal["depends_on"]) if proposal["depends_on"] else "-"
        lines.extend(
            [
                f"選択中 proposal: {proposal_id}",
                f"planner_role: {planner_role or '-'}",
                f"title: {proposal['title']}",
                f"state: {proposal['state']}",
                f"why_now: {proposal['why_now'] or '-'}",
                f"depends_on: {depends_on}",
                f"description: {proposal['description'] or '-'}",
                "",
                "[1] この proposal から task 作成",
                "[0] 戻る",
                "",
                "番号で入力してください",
            ]
        )
        return "\n".join(lines)

    def render_created_task_menu(
        self,
        *,
        created_task_id: str,
        last_message: str,
    ) -> str:
        lines = self._start_lines(last_message)
        lines.extend(
            [
                f"created_task_id: {created_task_id or '-'}",
                "",
                "[1] そのまま標準ライン自動実行",
                "[0] 戻る",
                "",
                "番号で入力してください",
            ]
        )
        return "\n".join(lines)

    def render_post_run_menu(
        self,
        *,
        task_id: str,
        status: str,
        last_message: str,
    ) -> str:
        lines = self._start_lines(last_message)

        if not task_id:
            lines.extend(
                [
                    "選択中 task がありません。",
                    "",
                    "[0] 戻る",
                    "",
                    "番号で入力してください",
                ]
            )
            return "\n".join(lines)

        if status == "completed":
            lines.extend(
                [
                    "次の操作を選んでください",
                    "",
                    "[1] 後工程メニューへ移動",
                    "[2] task 一覧へ移動",
                    "[3] メインメニューへ戻る",
                    "[0] 戻る",
                    "",
                    "番号で入力してください",
                ]
            )
            return "\n".join(lines)

        lines.extend(
            [
                "次の操作を選んでください",
                "",
                "[1] task 一覧へ移動",
                "[2] メインメニューへ戻る",
                "[0] 戻る",
                "",
                "番号で入力してください",
            ]
        )
        return "\n".join(lines)

    def render_post_pipeline_menu(
        self,
        *,
        source_task_id: str,
        source_task_status: str,
        approval_mode: str,
        stop_after_current_task_requested: bool,
        active_planner_role: str,
        last_planner_role: str,
        last_plan_director_decision: str,
        waiting_next_task_approval: bool,
        development_mode: str,
        last_message: str,
    ) -> str:
        lines = self._start_lines(last_message)

        normalized_source_task_id = str(source_task_id).strip() or "-"
        normalized_status = str(source_task_status).strip() or "-"
        normalized_approval_mode = str(approval_mode).strip() or "manual"
        normalized_active_planner_role = str(active_planner_role).strip() or "planner_safe"
        normalized_last_planner_role = str(last_planner_role).strip() or "planner_safe"
        normalized_decision = str(last_plan_director_decision).strip() or "-"
        normalized_development_mode = str(development_mode).strip() or "maintenance"
        stop_text = "ON" if bool(stop_after_current_task_requested) else "OFF"
        waiting_text = "あり" if bool(waiting_next_task_approval) else "なし"

        lines.extend(
            [
                "後工程メニュー",
                "",
                f"source task: {normalized_source_task_id}",
                f"status: {normalized_status}",
                f"development_mode: {normalized_development_mode}",
                f"active_planner_role: {normalized_active_planner_role}",
                f"approval_mode: {normalized_approval_mode}",
                f"stop_reservation: {stop_text}",
                f"last_planner_role: {normalized_last_planner_role}",
                f"last_plan_director_decision: {normalized_decision}",
                f"waiting_next_task_approval: {waiting_text}",
                "",
                "[1] planner を実行",
                "[2] plan_director を実行",
                "[3] planner → plan_director を自動実行",
                "[4] 承認待ちを確認",
                "[5] pipeline 設定",
                "[6] task 一覧へ移動",
                "[7] メインメニューへ戻る",
                "[0] 戻る",
                "",
                "番号で入力してください",
            ]
        )
        return "\n".join(lines)

    def render_plan_director_result_menu(
        self,
        *,
        source_task_id: str,
        decision: str,
        selected_proposal_id: str,
        selected_planner_role: str,
        selection_reason: str,
        approval_mode: str,
        waiting_next_task_approval: bool,
        last_message: str,
    ) -> str:
        lines = self._start_lines(last_message)

        normalized_source_task_id = str(source_task_id).strip() or "-"
        normalized_decision = str(decision).strip() or "-"
        normalized_selected_proposal_id = str(selected_proposal_id).strip() or "-"
        normalized_selected_planner_role = str(selected_planner_role).strip() or "-"
        normalized_selection_reason = str(selection_reason).strip() or "-"
        normalized_approval_mode = str(approval_mode).strip() or "manual"
        waiting_text = "あり" if bool(waiting_next_task_approval) else "なし"

        lines.extend(
            [
                "plan_director 実行結果",
                "",
                f"source task: {normalized_source_task_id}",
                f"decision: {normalized_decision}",
                f"selected_proposal_id: {normalized_selected_proposal_id}",
                f"selected_planner_role: {normalized_selected_planner_role}",
                f"selection_reason: {normalized_selection_reason}",
                f"approval_mode: {normalized_approval_mode}",
                f"waiting_next_task_approval: {waiting_text}",
                "",
            ]
        )

        if normalized_decision == "adopt":
            lines.extend(
                [
                    "[1] 承認待ちへ進む / 確認する",
                    "[2] 後工程メニューへ戻る",
                    "[3] task 一覧へ移動",
                    "[0] 戻る",
                    "",
                    "番号で入力してください",
                ]
            )
            return "\n".join(lines)

        lines.extend(
            [
                "[1] 後工程メニューへ戻る",
                "[2] task 一覧へ移動",
                "[0] 戻る",
                "",
                "番号で入力してください",
            ]
        )
        return "\n".join(lines)

    def render_next_task_approval_menu(
        self,
        *,
        source_task_id: str,
        decision: str,
        selected_proposal_id: str,
        selected_planner_role: str,
        selection_reason: str,
        last_message: str,
    ) -> str:
        lines = self._start_lines(last_message)

        normalized_source_task_id = str(source_task_id).strip() or "-"
        normalized_decision = str(decision).strip() or "-"
        normalized_selected_proposal_id = str(selected_proposal_id).strip() or "-"
        normalized_selected_planner_role = str(selected_planner_role).strip() or "-"
        normalized_selection_reason = str(selection_reason).strip() or "-"

        lines.extend(
            [
                "次 task 承認待ち",
                "",
                f"source task: {normalized_source_task_id}",
                f"decision: {normalized_decision}",
                f"selected_proposal_id: {normalized_selected_proposal_id}",
                f"selected_planner_role: {normalized_selected_planner_role}",
                f"selection_reason: {normalized_selection_reason}",
                "",
                "[1] 次 task 作成を承認",
                "[2] 今回は作成しない",
                "[3] 後工程メニューへ戻る",
                "[0] 戻る",
                "",
                "番号で入力してください",
            ]
        )
        return "\n".join(lines)

    def render_pipeline_settings_menu(
        self,
        *,
        active_planner_role: str,
        approval_mode: str,
        stop_after_current_task_requested: bool,
        development_mode: str,
        last_message: str,
    ) -> str:
        lines = self._start_lines(last_message)
        stop_text = "ON" if bool(stop_after_current_task_requested) else "OFF"

        lines.extend(
            [
                "pipeline 設定",
                "",
                f"active_planner_role: {active_planner_role or '-'}",
                f"approval_mode: {approval_mode or '-'}",
                f"stop_reservation: {stop_text}",
                f"development_mode: {development_mode or '-'}",
                "",
                "[1] planner_role を planner_safe にする",
                "[2] planner_role を planner_improvement にする",
                "[3] approval_mode を manual にする",
                "[4] approval_mode を auto にする",
                "[5] stop_reservation を切り替える",
                "[6] development_mode を maintenance にする",
                "[7] development_mode を mainline にする",
                "[0] 戻る",
                "",
                "番号で入力してください",
            ]
        )
        return "\n".join(lines)

    def render_exited_menu(self, *, last_message: str) -> str:
        lines = self._start_lines(last_message)
        lines.extend(
            [
                "Remote Operator は終了状態です。",
                "",
                "[0] メインメニューへ戻る",
                "",
                "番号で入力してください",
            ]
        )
        return "\n".join(lines)

    def _start_lines(self, last_message: str, title: str = "") -> list[str]:
        lines: list[str] = []
        if title:
            lines.append(title)
            lines.append("")
        if last_message:
            lines.append(last_message)
            lines.append("")
        return lines
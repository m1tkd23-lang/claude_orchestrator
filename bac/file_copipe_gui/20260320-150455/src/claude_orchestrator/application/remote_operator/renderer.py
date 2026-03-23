# src\claude_orchestrator\application\remote_operator\renderer.py
from __future__ import annotations


class RemoteOperatorRenderer:
    def render_main_menu(self, *, last_message: str) -> str:
        lines = self._start_lines(last_message)
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
                    "0. 戻る",
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
                "0. 戻る",
                "",
                "番号で入力してください",
            ]
        )
        return "\n".join(lines)

    def render_proposal_list_menu(
        self,
        *,
        source_task_id: str,
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
                    "0. 戻る",
                    "",
                    "番号で入力してください",
                ]
            )
            return "\n".join(lines)

        lines.extend(
            [
                title,
                "",
            ]
        )

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

    def render_selected_proposal_menu(
        self,
        *,
        proposal_id: str,
        proposal: dict | None,
        last_message: str,
    ) -> str:
        lines = self._start_lines(last_message)

        if proposal is None:
            lines.extend(
                [
                    f"{proposal_id or 'proposal'} が見つかりません。",
                    "",
                    "0. 戻る",
                    "",
                    "番号で入力してください",
                ]
            )
            return "\n".join(lines)

        depends_on = ", ".join(proposal["depends_on"]) if proposal["depends_on"] else "-"
        lines.extend(
            [
                f"選択中 proposal: {proposal_id}",
                f"title: {proposal['title']}",
                f"state: {proposal['state']}",
                f"why_now: {proposal['why_now'] or '-'}",
                f"depends_on: {depends_on}",
                f"description: {proposal['description'] or '-'}",
                "",
                "1. この proposal から task 作成",
                "0. 戻る",
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
                "1. そのまま実行",
                "0. 戻る",
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
                    "0. 戻る",
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
                    "1. 次タスク案を作成する",
                    "2. task 一覧へ移動",
                    "3. メインメニューへ戻る",
                    "0. 戻る",
                    "",
                    "番号で入力してください",
                ]
            )
            return "\n".join(lines)

        lines.extend(
            [
                "次の操作を選んでください",
                "",
                "1. task 一覧へ移動",
                "2. メインメニューへ戻る",
                "0. 戻る",
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
                "0. メインメニューへ戻る",
                "",
                "番号で入力してください",
            ]
        )
        return "\n".join(lines)

    @staticmethod
    def _start_lines(last_message: str, title: str = "") -> list[str]:
        normalized_message = str(last_message).strip()
        normalized_title = str(title).strip()
        if not normalized_message:
            return []
        if normalized_title and normalized_message == normalized_title:
            return []
        return [normalized_message, ""]
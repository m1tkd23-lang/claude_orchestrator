# src\claude_orchestrator\application\usecases\advance_task_usecase.py
from __future__ import annotations

from pathlib import Path
import json
from datetime import datetime

from claude_orchestrator.application.usecases.validate_report_usecase import (
    ValidateReportUseCase,
)
from claude_orchestrator.core.task_factory import write_json
from claude_orchestrator.core.workflow import decide_next_from_report
from claude_orchestrator.infrastructure.task_runtime import TaskRuntime


class AdvanceTaskUseCase:
    MAX_HISTORY_BLOCKS = 20
    MAX_RISKS = 5

    def execute(
        self,
        repo_path: str,
        task_id: str,
        expected_role: str,
        expected_cycle: int,
        expected_revision: int,
    ) -> dict:
        target_repo = Path(repo_path).resolve()
        runtime = TaskRuntime(target_repo=target_repo, task_id=task_id)

        state_json = runtime.load_state_json()
        current_role = str(state_json["next_role"])
        current_cycle = int(state_json["cycle"])
        current_revision = int(state_json.get("revision", 1))
        max_cycles = int(state_json["max_cycles"])

        if current_role == "none":
            raise ValueError(f"Task already finished or blocked: {task_id}")

        if current_role != str(expected_role):
            raise ValueError(
                f"state drift detected: expected_role={expected_role}, actual_role={current_role}"
            )

        if current_cycle != int(expected_cycle):
            raise ValueError(
                f"state drift detected: expected_cycle={expected_cycle}, actual_cycle={current_cycle}"
            )

        if current_revision != int(expected_revision):
            raise ValueError(
                f"state revision mismatch: expected_revision={expected_revision}, actual_revision={current_revision}"
            )

        ValidateReportUseCase().execute(
            repo_path=repo_path,
            task_id=task_id,
            role=current_role,
            expected_cycle=current_cycle,
            expected_revision=current_revision,
        )

        report_path = runtime.get_output_json_path(current_role, current_cycle)
        with report_path.open("r", encoding="utf-8") as f:
            report = json.load(f)

        if current_role == "task_router":
            self._apply_task_router_result(runtime=runtime, report=report)

        if current_role == "director" and report.get("final_action") == "approve":
            self._append_task_history(
                runtime=runtime,
                repo_path=target_repo,
                task_id=task_id,
                cycle=current_cycle,
            )

        next_state_values = decide_next_from_report(
            role=current_role,
            report=report,
            current_cycle=current_cycle,
            max_cycles=max_cycles,
        )

        new_state = dict(state_json)
        new_state["cycle"] = next_state_values["cycle"]
        new_state["revision"] = current_revision + 1
        new_state["status"] = next_state_values["status"]
        new_state["current_stage"] = next_state_values["current_stage"]
        new_state["next_role"] = next_state_values["next_role"]
        new_state["last_completed_role"] = next_state_values["last_completed_role"]

        write_json(runtime.state_json_path, new_state)

        return {
            "task_id": task_id,
            "status": new_state["status"],
            "current_stage": new_state["current_stage"],
            "next_role": new_state["next_role"],
            "cycle": new_state["cycle"],
            "revision": new_state["revision"],
            "state_path": str(runtime.state_json_path),
        }

    def _append_task_history(
        self,
        *,
        runtime: TaskRuntime,
        repo_path: Path,
        task_id: str,
        cycle: int,
    ) -> None:
        base_dir = repo_path / ".claude_orchestrator" / "docs" / "task_history"
        history_path = base_dir / "過去TASK作業記録.md"
        archive_dir = base_dir / "archive"
        archive_path = archive_dir / "task_history_archive.md"

        base_dir.mkdir(parents=True, exist_ok=True)
        archive_dir.mkdir(parents=True, exist_ok=True)

        task_json = runtime.load_task_json()

        implementer = self._safe_load(runtime.get_output_json_path("implementer", cycle))
        director = self._safe_load(runtime.get_output_json_path("director", cycle))

        now = datetime.now().strftime("%Y-%m-%d %H:%M")

        summary = self._shorten(implementer.get("summary", ""), 120)
        risks = director.get("remaining_risks", [])[: self.MAX_RISKS]

        entry = (
            f"\n## {task_id} : {task_json.get('title', '')}\n\n"
            f"- 実行日時: {now}\n"
            f"- task_type: {task_json.get('task_type')}\n"
            f"- risk_level: {task_json.get('risk_level')}\n\n"
            f"### 変更内容\n{summary}\n\n"
            f"### 関連ファイル\n{self._format_list(implementer.get('changed_files', []))}\n\n"
            f"### 注意点\n{self._format_list(risks)}\n"
        )

        if history_path.exists():
            text = history_path.read_text(encoding="utf-8").rstrip()
        else:
            text = (
                "# 過去TASK作業記録\n\n"
                "## 目的\n"
                "plannerが次タスクを判断するための短い知見のみを残す\n\n"
                "---"
            )

        text += "\n" + entry
        history_path.write_text(text, encoding="utf-8")

        self._trim_history(history_path, archive_path)

    def _trim_history(self, history_path: Path, archive_path: Path) -> None:
        text = history_path.read_text(encoding="utf-8")

        lines = text.splitlines()
        blocks = []
        current = []

        for line in lines:
            if line.startswith("## TASK-") and current:
                blocks.append("\n".join(current))
                current = []
            current.append(line)

        if current:
            blocks.append("\n".join(current))

        if len(blocks) <= 1:
            return

        header = blocks[0]
        tasks = blocks[1:]

        if len(tasks) <= self.MAX_HISTORY_BLOCKS:
            return

        overflow = tasks[:-self.MAX_HISTORY_BLOCKS]
        remain = tasks[-self.MAX_HISTORY_BLOCKS:]

        if archive_path.exists():
            archive_text = archive_path.read_text(encoding="utf-8").rstrip()
        else:
            archive_text = "# Task History Archive\n\n---"

        archive_text += "\n\n" + "\n\n".join(overflow)
        archive_path.write_text(archive_text, encoding="utf-8")

        new_text = header + "\n\n" + "\n\n".join(remain)
        history_path.write_text(new_text, encoding="utf-8")

    @staticmethod
    def _shorten(text: str, limit: int = 120) -> str:
        return text if len(text) <= limit else text[:limit] + "..."

    @staticmethod
    def _safe_load(path: Path) -> dict:
        if not path.exists():
            return {}
        with path.open("r", encoding="utf-8") as f:
            return json.load(f)

    @staticmethod
    def _format_list(values: list) -> str:
        if not values:
            return "- none"
        return "\n".join(f"- {v}" for v in values)

    @staticmethod
    def _apply_task_router_result(runtime: TaskRuntime, report: dict) -> None:
        task_json = runtime.load_task_json()
        updated_task = dict(task_json)

        role_skill_plan = report.get("role_skill_plan", {}) or {}

        updated_task["task_type"] = report.get("task_type")
        updated_task["risk_level"] = report.get("risk_level")
        updated_task["role_skill_plan"] = {
            "task_router": ["route-task"],
            "implementer": list(role_skill_plan.get("implementer", [])),
            "reviewer": list(role_skill_plan.get("reviewer", [])),
            "director": list(role_skill_plan.get("director", [])),
        }

        write_json(runtime.task_json_path, updated_task)
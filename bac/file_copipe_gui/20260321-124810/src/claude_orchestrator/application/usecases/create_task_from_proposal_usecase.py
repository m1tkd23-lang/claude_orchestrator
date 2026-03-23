# src\claude_orchestrator\application\usecases\create_task_from_proposal_usecase.py
from __future__ import annotations

from pathlib import Path
import json
import re

from claude_orchestrator.application.usecases.create_task_usecase import (
    CreateTaskUseCase,
)
from claude_orchestrator.infrastructure.planner_runtime import PlannerRuntime


class CreateTaskFromProposalUseCase:
    def execute(
        self,
        *,
        repo_path: str,
        source_task_id: str,
        proposal_id: str,
        planner_role: str = "planner_safe",
    ) -> dict:
        target_repo = Path(repo_path).resolve()
        runtime = PlannerRuntime(
            target_repo=target_repo,
            source_task_id=source_task_id,
        )
        planner_role = runtime.validate_planner_role(planner_role)

        runtime.ensure_source_task_exists()

        state_json = runtime.load_source_state_json()
        cycle = int(state_json["cycle"])
        report_path = runtime.get_report_path(cycle=cycle, planner_role=planner_role)

        if not report_path.exists():
            raise FileNotFoundError(f"Planner report not found: {report_path}")

        planner_report = self._load_json(report_path)
        proposal = self._find_proposal(planner_report, proposal_id)
        fields = self._proposal_to_task_fields(proposal)

        # ===== carry_over-v1 =====
        director_report_path = (
            target_repo
            / ".claude_orchestrator"
            / "tasks"
            / source_task_id
            / "inbox"
            / f"director_report_v{cycle}.json"
        )

        carry_over_context_files = list(fields["context_files"])
        carry_over_items: list[str] = []

        if director_report_path.exists():
            director_report = self._load_json(director_report_path)
            remaining_risks = director_report.get("remaining_risks", []) or []

            carry_over_items = self._filter_carry_over_items(remaining_risks)

            # context_files に追加（重複防止）
            rel_path = (
                f".claude_orchestrator/tasks/{source_task_id}/inbox/"
                f"director_report_v{cycle}.json"
            )
            if rel_path not in carry_over_context_files:
                carry_over_context_files.append(rel_path)

        # task作成
        created_task_dir = CreateTaskUseCase().execute(
            repo_path=repo_path,
            title=fields["title"],
            description=fields["description"],
            context_files=carry_over_context_files,
            constraints=fields["constraints"],
        )
        created_task_id = Path(created_task_dir).name

        # proposal state 更新
        state_path = runtime.planner_dir / f"{planner_role}_proposal_states_v{cycle}.json"
        self._set_proposal_state(
            state_path=state_path,
            source_task_id=source_task_id,
            cycle=cycle,
            proposal_id=proposal_id,
            state="task_created",
        )

        return {
            "source_task_id": source_task_id,
            "planner_role": planner_role,
            "proposal_id": proposal_id,
            "created_task_id": created_task_id,
            "created_task_dir": str(created_task_dir),
            "planner_report_path": str(report_path),
            "proposal_state_path": str(state_path),
            "carry_over_items": carry_over_items,
        }

    # ==========================
    # carry_over フィルタ
    # ==========================
    @staticmethod
    def _filter_carry_over_items(items: list[str]) -> list[str]:
        result: list[str] = []
        seen: set[str] = set()

        pattern = re.compile(r"^\[carry_over from TASK-\d+\]")

        for item in items:
            text = str(item).strip()
            if not text:
                continue

            # 過去carry_overは除外
            if pattern.match(text):
                continue

            # 重複除外
            if text in seen:
                continue

            seen.add(text)
            result.append(text)

        return result

    @staticmethod
    def _load_json(path: Path) -> dict:
        with path.open("r", encoding="utf-8") as f:
            return json.load(f)

    @staticmethod
    def _find_proposal(planner_report: dict, proposal_id: str) -> dict:
        normalized = str(proposal_id).strip()
        for proposal in planner_report.get("proposals", []):
            if str(proposal.get("proposal_id", "")).strip() == normalized:
                return proposal
        raise ValueError(f"Proposal not found: {proposal_id}")

    @staticmethod
    def _proposal_to_task_fields(proposal: dict) -> dict:
        title = str(proposal.get("title", "")).strip()
        description = str(proposal.get("description", "")).strip()
        why_now = str(proposal.get("why_now", "")).strip()
        depends_on = [
            str(x).strip()
            for x in (proposal.get("depends_on", []) or [])
            if str(x).strip()
        ]
        context_files = [
            str(x).strip()
            for x in (proposal.get("context_files", []) or [])
            if str(x).strip()
        ]
        constraints = [
            str(x).strip()
            for x in (proposal.get("constraints", []) or [])
            if str(x).strip()
        ]

        if not title:
            raise ValueError("Proposal title is empty.")
        if not description:
            raise ValueError("Proposal description is empty.")

        description_lines = [description]
        if why_now:
            description_lines.extend(["", "[why_now]", why_now])

        merged_constraints = list(constraints)
        for item in depends_on:
            merged_constraints.append(f"depends_on: {item}")

        return {
            "title": title,
            "description": "\n".join(description_lines).strip(),
            "context_files": context_files,
            "constraints": merged_constraints,
        }

    @staticmethod
    def _set_proposal_state(
        *,
        state_path: Path,
        source_task_id: str,
        cycle: int,
        proposal_id: str,
        state: str,
    ) -> None:
        if state not in {
            "proposed",
            "accepted",
            "rejected",
            "deferred",
            "task_created",
        }:
            raise ValueError(f"Unsupported proposal state: {state}")

        if state_path.exists():
            with state_path.open("r", encoding="utf-8") as f:
                payload = json.load(f)
        else:
            payload = {
                "source_task_id": source_task_id,
                "cycle": cycle,
                "proposal_states": [],
            }

        proposal_states = payload.setdefault("proposal_states", [])

        found = False
        for item in proposal_states:
            if str(item.get("proposal_id", "")).strip() == str(proposal_id).strip():
                item["state"] = state
                found = True
                break

        if not found:
            proposal_states.append(
                {
                    "proposal_id": str(proposal_id).strip(),
                    "state": state,
                }
            )

        state_path.parent.mkdir(parents=True, exist_ok=True)
        with state_path.open("w", encoding="utf-8") as f:
            json.dump(payload, f, ensure_ascii=False, indent=2)
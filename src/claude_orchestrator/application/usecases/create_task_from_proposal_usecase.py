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
    CARRY_OVER_PREFIX_PATTERN = re.compile(r"^\[carry_over from TASK-\d+\]")
    MAX_CARRY_OVER_ITEMS = 5

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
        fields = self._proposal_to_task_fields(
            proposal=proposal,
            source_task_id=source_task_id,
            source_cycle=cycle,
            target_repo=target_repo,
        )

        created_task_dir = CreateTaskUseCase().execute(
            repo_path=repo_path,
            title=fields["title"],
            description=fields["description"],
            context_files=fields["context_files"],
            constraints=fields["constraints"],
            initial_execution_notes=fields["initial_execution_notes"],
        )
        created_task_id = Path(created_task_dir).name

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
            "carry_over_items_count": len(fields["initial_execution_notes"]),
        }

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

    @classmethod
    def _proposal_to_task_fields(
        cls,
        *,
        proposal: dict,
        source_task_id: str,
        source_cycle: int,
        target_repo: Path,
    ) -> dict:
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
            description_lines.extend(
                [
                    "",
                    "[why_now]",
                    why_now,
                ]
            )

        merged_constraints = list(constraints)
        for item in depends_on:
            merged_constraints.append(f"depends_on: {item}")

        merged_context_files, carry_over_notes = cls._build_carry_over_fields(
            proposal_context_files=context_files,
            source_task_id=source_task_id,
            source_cycle=source_cycle,
            target_repo=target_repo,
        )

        return {
            "title": title,
            "description": "\n".join(description_lines).strip(),
            "context_files": merged_context_files,
            "constraints": merged_constraints,
            "initial_execution_notes": carry_over_notes,
        }

    @classmethod
    def _build_carry_over_fields(
        cls,
        *,
        proposal_context_files: list[str],
        source_task_id: str,
        source_cycle: int,
        target_repo: Path,
    ) -> tuple[list[str], list[str]]:
        merged_context_files: list[str] = []
        seen_context_files: set[str] = set()

        def add_context_if_missing(path_text: str) -> None:
            normalized = str(path_text).strip()
            if not normalized or normalized in seen_context_files:
                return
            seen_context_files.add(normalized)
            merged_context_files.append(normalized)

        for item in proposal_context_files:
            add_context_if_missing(item)

        director_report_rel = (
            f".claude_orchestrator/tasks/{source_task_id}/inbox/"
            f"director_report_v{source_cycle}.json"
        )
        director_report_abs = target_repo / director_report_rel

        carry_over_notes: list[str] = []

        # carry_over-v2:
        # - director_report が存在する場合のみ carry_over 処理を行う
        # - 再carry_overは禁止
        # - 完全一致重複は除去
        # - 最大件数は MAX_CARRY_OVER_ITEMS
        if director_report_abs.exists():
            add_context_if_missing(director_report_rel)

            director_report = cls._load_json(director_report_abs)
            remaining_risks = director_report.get("remaining_risks", []) or []

            filtered_items = cls._filter_remaining_risks_for_carry_over(
                remaining_risks=remaining_risks
            )

            carry_over_notes = [
                f"[carry_over from {source_task_id}] {item}" for item in filtered_items
            ]

        return merged_context_files, carry_over_notes

    @classmethod
    def _filter_remaining_risks_for_carry_over(
        cls,
        *,
        remaining_risks: list[object],
    ) -> list[str]:
        unique_items: list[str] = []
        seen: set[str] = set()

        for item in remaining_risks:
            text = str(item).strip()
            if not text:
                continue

            # v2: すでに carry_over 済みの項目は再転記しない
            if cls.CARRY_OVER_PREFIX_PATTERN.match(text):
                continue

            # v2: 完全一致重複を除去
            if text in seen:
                continue

            seen.add(text)
            unique_items.append(text)

        # v2: 最大件数に制限
        return unique_items[: cls.MAX_CARRY_OVER_ITEMS]

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
            f.write("\n")
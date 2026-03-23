# src\claude_orchestrator\application\usecases\create_task_from_proposal_usecase.py
from __future__ import annotations

from pathlib import Path
import json

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

        merged_context_files = cls._merge_context_files(
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
        }

    @staticmethod
    def _merge_context_files(
        *,
        proposal_context_files: list[str],
        source_task_id: str,
        source_cycle: int,
        target_repo: Path,
    ) -> list[str]:
        merged: list[str] = []
        seen: set[str] = set()

        def add_if_missing(path_text: str) -> None:
            normalized = str(path_text).strip()
            if not normalized or normalized in seen:
                return
            seen.add(normalized)
            merged.append(normalized)

        for item in proposal_context_files:
            add_if_missing(item)

        director_report_rel = (
            f".claude_orchestrator/tasks/{source_task_id}/inbox/"
            f"director_report_v{source_cycle}.json"
        )
        director_report_abs = target_repo / director_report_rel

        # carry_over-v1:
        # plan_director 採択から生成される次 task が、
        # 前 task の director_report を context_files 経由で参照できるようにする。
        # report が存在しない場合は task 作成を止めず、既存 proposal の内容だけで継続する。
        if director_report_abs.exists():
            add_if_missing(director_report_rel)

        return merged

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
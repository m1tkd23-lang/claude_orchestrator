# src\claude_orchestrator\application\usecases\list_proposals_usecase.py
from __future__ import annotations

from pathlib import Path
import json

from claude_orchestrator.infrastructure.planner_runtime import PlannerRuntime


class ListProposalsUseCase:
    def execute(
        self,
        *,
        repo_path: str,
        source_task_id: str,
    ) -> dict:
        target_repo = Path(repo_path).resolve()
        runtime = PlannerRuntime(
            target_repo=target_repo,
            source_task_id=source_task_id,
        )

        runtime.ensure_source_task_exists()

        state_json = runtime.load_source_state_json()
        cycle = int(state_json["cycle"])
        report_path = runtime.get_report_path(cycle)

        if not report_path.exists():
            raise FileNotFoundError(f"Planner report not found: {report_path}")

        planner_report = self._load_json(report_path)
        state_path = runtime.planner_dir / f"proposal_states_v{cycle}.json"
        state_map = self._load_proposal_state_map(state_path)

        proposals_out: list[dict] = []
        for proposal in planner_report.get("proposals", []):
            proposal_id = str(proposal.get("proposal_id", "")).strip()
            proposals_out.append(
                {
                    "proposal_id": proposal_id,
                    "title": str(proposal.get("title", "")).strip(),
                    "description": str(proposal.get("description", "")).strip(),
                    "why_now": str(proposal.get("why_now", "")).strip(),
                    "depends_on": list(proposal.get("depends_on", []) or []),
                    "context_files": list(proposal.get("context_files", []) or []),
                    "constraints": list(proposal.get("constraints", []) or []),
                    "state": state_map.get(proposal_id, "proposed"),
                }
            )

        return {
            "source_task_id": source_task_id,
            "cycle": cycle,
            "summary": str(planner_report.get("summary", "")).strip(),
            "report_path": str(report_path),
            "state_path": str(state_path),
            "proposals": proposals_out,
        }

    @staticmethod
    def _load_json(path: Path) -> dict:
        with path.open("r", encoding="utf-8") as f:
            return json.load(f)

    @staticmethod
    def _load_proposal_state_map(path: Path) -> dict[str, str]:
        if not path.exists():
            return {}

        with path.open("r", encoding="utf-8") as f:
            payload = json.load(f)

        result: dict[str, str] = {}
        for item in payload.get("proposal_states", []):
            proposal_id = str(item.get("proposal_id", "")).strip()
            state = str(item.get("state", "proposed")).strip() or "proposed"
            if proposal_id:
                result[proposal_id] = state
        return result
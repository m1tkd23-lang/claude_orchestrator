# src\claude_orchestrator\gui\proposal_state_store.py
from __future__ import annotations

from pathlib import Path
import json


class ProposalStateStore:
    def __init__(self, *, repo_path: str, source_task_id: str, cycle: int) -> None:
        self.repo_path = Path(repo_path).resolve()
        self.source_task_id = source_task_id
        self.cycle = int(cycle)
        self.planner_dir = (
            self.repo_path
            / ".claude_orchestrator"
            / "tasks"
            / source_task_id
            / "planner"
        )
        self.state_path = self.planner_dir / f"proposal_states_v{self.cycle}.json"

    def initialize_from_report(self, planner_report: dict) -> None:
        proposals = planner_report.get("proposals", [])
        payload = {
            "source_task_id": self.source_task_id,
            "cycle": self.cycle,
            "proposal_states": [
                {
                    "proposal_id": str(proposal.get("proposal_id", "")),
                    "state": "proposed",
                }
                for proposal in proposals
            ],
        }
        self._write_json(payload)

    def load(self) -> dict:
        if not self.state_path.exists():
            return {
                "source_task_id": self.source_task_id,
                "cycle": self.cycle,
                "proposal_states": [],
            }
        with self.state_path.open("r", encoding="utf-8") as f:
            return json.load(f)

    def get_state_map(self) -> dict[str, str]:
        payload = self.load()
        result: dict[str, str] = {}
        for item in payload.get("proposal_states", []):
            proposal_id = str(item.get("proposal_id", "")).strip()
            state = str(item.get("state", "proposed")).strip() or "proposed"
            if proposal_id:
                result[proposal_id] = state
        return result

    def set_state(self, proposal_id: str, state: str) -> None:
        if state not in {"proposed", "accepted", "rejected", "deferred"}:
            raise ValueError(f"Unsupported proposal state: {state}")

        payload = self.load()
        proposal_states = payload.setdefault("proposal_states", [])

        found = False
        for item in proposal_states:
            if str(item.get("proposal_id")) == proposal_id:
                item["state"] = state
                found = True
                break

        if not found:
            proposal_states.append(
                {
                    "proposal_id": proposal_id,
                    "state": state,
                }
            )

        self._write_json(payload)

    def _write_json(self, payload: dict) -> None:
        self.planner_dir.mkdir(parents=True, exist_ok=True)
        with self.state_path.open("w", encoding="utf-8") as f:
            json.dump(payload, f, ensure_ascii=False, indent=2)
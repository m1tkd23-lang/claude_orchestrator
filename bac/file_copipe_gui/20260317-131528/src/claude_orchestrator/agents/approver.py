# src\claude_orchestrator\agents\approver.py
from __future__ import annotations

from pathlib import Path

from claude_orchestrator.agents.base import BaseAgent
from claude_orchestrator.models.report import ApproverReport, ReviewerReport


class ApproverAgent(BaseAgent):
    def __init__(self, name: str, repo_path: Path) -> None:
        super().__init__(name=name, repo_path=repo_path)

    def run(self, reviewer_report: ReviewerReport) -> ApproverReport:
        _ = reviewer_report

        return ApproverReport(
            final_decision="approved",
            summary="dummy approval",
            remaining_risks=[],
        )
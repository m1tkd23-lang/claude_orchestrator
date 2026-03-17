# src\claude_orchestrator\agents\reviewer.py
from __future__ import annotations

from pathlib import Path

from claude_orchestrator.agents.base import BaseAgent
from claude_orchestrator.models.report import ImplementerReport, ReviewerReport


class ReviewerAgent(BaseAgent):
    def __init__(self, name: str, repo_path: Path) -> None:
        super().__init__(name=name, repo_path=repo_path)

    def run(self, implementer_report: ImplementerReport) -> ReviewerReport:
        _ = implementer_report

        return ReviewerReport(
            decision="ok",
            summary="dummy review result",
            must_fix=[],
            nice_to_have=[],
        )
# src\claude_orchestrator\agents\implementer.py
from __future__ import annotations

from pathlib import Path

from claude_orchestrator.agents.base import BaseAgent
from claude_orchestrator.models.report import ImplementerReport


class ImplementerAgent(BaseAgent):
    def __init__(self, name: str, repo_path: Path) -> None:
        super().__init__(name=name, repo_path=repo_path)

    def run(self, task: str) -> ImplementerReport:
        return ImplementerReport(
            status="done",
            summary="dummy implement result",
            task=task,
            changed_files=[],
            commands_run=[],
            test_results=[],
            risks=[],
        )
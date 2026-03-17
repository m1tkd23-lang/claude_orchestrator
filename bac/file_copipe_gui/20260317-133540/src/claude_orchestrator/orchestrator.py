# src\claude_orchestrator\orchestrator.py
from __future__ import annotations

from datetime import datetime
import json
from pathlib import Path

from claude_orchestrator.agents.approver import ApproverAgent
from claude_orchestrator.agents.implementer import ImplementerAgent
from claude_orchestrator.agents.reviewer import ReviewerAgent
from claude_orchestrator.config import AppConfig, TargetConfig
from claude_orchestrator.models.job import Job
from claude_orchestrator.models.report import (
    ApproverReport,
    ImplementerReport,
    ReviewerReport,
)
from claude_orchestrator.services.claude_service import ClaudeService


class Orchestrator:
    def __init__(self, app_config: AppConfig, target_config: TargetConfig) -> None:
        self.app_config = app_config
        self.target_config = target_config

        self.report_dir = Path(self.app_config.report_dir)
        self.report_dir.mkdir(parents=True, exist_ok=True)

        claude_service = ClaudeService(setting_sources=["project"])

        prompt_root = Path("src/claude_orchestrator/prompts")

        self.implementer = ImplementerAgent(
            name=self.app_config.agent.implementer,
            repo_path=self.target_config.repo_path,
            claude_service=claude_service,
            prompt_path=prompt_root / "implementer.md",
        )
        self.reviewer = ReviewerAgent(
            name=self.app_config.agent.reviewer,
            repo_path=self.target_config.repo_path,
            claude_service=claude_service,
            prompt_path=prompt_root / "reviewer.md",
        )
        self.approver = ApproverAgent(
            name=self.app_config.agent.approver,
            repo_path=self.target_config.repo_path,
            claude_service=claude_service,
            prompt_path=prompt_root / "approver.md",
        )

    def run(self, job: Job) -> None:
        print("=== ORCHESTRATOR START ===")
        print("target repo:", self.target_config.repo_path)
        print("target name:", self.target_config.target_name)
        print("task:", job.task)

        implement_result = self.run_implementer(job)
        review_result = self.run_reviewer(implement_result)
        approval_result = self.run_approver(review_result)

        self.save_report(
            implement_result=implement_result,
            review_result=review_result,
            approval_result=approval_result,
        )

    def run_implementer(self, job: Job) -> ImplementerReport:
        print(f"{self.implementer.name} running")
        return self.implementer.run(task=job.task)

    def run_reviewer(self, implement_result: ImplementerReport) -> ReviewerReport:
        print(f"{self.reviewer.name} running")
        return self.reviewer.run(implementer_report=implement_result)

    def run_approver(self, review_result: ReviewerReport) -> ApproverReport:
        print(f"{self.approver.name} running")
        return self.approver.run(reviewer_report=review_result)

    def save_report(
        self,
        implement_result: ImplementerReport,
        review_result: ReviewerReport,
        approval_result: ApproverReport,
    ) -> None:
        ts = datetime.now().strftime("%Y%m%d_%H%M%S")

        report = {
            "target_name": self.target_config.target_name,
            "repo_path": str(self.target_config.repo_path),
            "implementer": implement_result.to_dict(),
            "reviewer": review_result.to_dict(),
            "approver": approval_result.to_dict(),
        }

        report_path = self.report_dir / f"report_{ts}.json"

        with report_path.open("w", encoding="utf-8") as f:
            json.dump(report, f, indent=2, ensure_ascii=False)

        print("report saved:", report_path)
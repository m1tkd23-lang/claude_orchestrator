# src\claude_orchestrator\orchestrator.py
from pathlib import Path
from datetime import datetime
import json


class Orchestrator:

    def __init__(self, target_repo: Path, report_dir: Path):
        self.target_repo = target_repo
        self.report_dir = report_dir

    def run(self, task: str):

        print("=== ORCHESTRATOR START ===")
        print("target repo:", self.target_repo)
        print("task:", task)

        implement_result = self.run_implementer(task)
        review_result = self.run_reviewer(implement_result)
        approval_result = self.run_approver(review_result)

        self.save_report(
            implement_result,
            review_result,
            approval_result
        )

    def run_implementer(self, task: str):

        print("implementer running")

        result = {
            "status": "done",
            "summary": "dummy implement result",
            "task": task,
            "changed_files": []
        }

        return result

    def run_reviewer(self, implement_result):

        print("reviewer running")

        result = {
            "decision": "ok",
            "summary": "dummy review result"
        }

        return result

    def run_approver(self, review_result):

        print("approver running")

        result = {
            "final_decision": "approved",
            "summary": "dummy approval"
        }

        return result

    def save_report(self, impl, review, approval):

        ts = datetime.now().strftime("%Y%m%d_%H%M%S")

        report = {
            "implementer": impl,
            "reviewer": review,
            "approver": approval
        }

        path = self.report_dir / f"report_{ts}.json"

        with open(path, "w", encoding="utf-8") as f:
            json.dump(report, f, indent=2, ensure_ascii=False)

        print("report saved:", path)
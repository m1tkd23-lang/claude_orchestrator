# src\claude_orchestrator\application\usecases\run_requirements_refinement_loop_usecase.py
from __future__ import annotations

from typing import Any

from claude_orchestrator.application.usecases.review_requirements_usecase import (
    ReviewRequirementsUseCase,
)
from claude_orchestrator.application.usecases.refine_requirements_usecase import (
    RefineRequirementsUseCase,
)


class RunRequirementsRefinementLoopUseCase:
    MAX_ITERATIONS = 3

    def execute(self, repo_path: str) -> dict[str, Any]:
        review_usecase = ReviewRequirementsUseCase()
        refine_usecase = RefineRequirementsUseCase()

        logs: list[dict[str, Any]] = []

        for iteration in range(1, self.MAX_ITERATIONS + 1):
            # --- review ---
            review_result = review_usecase.execute(repo_path=repo_path)
            review_json = review_result["review"]

            issues = review_json.get("issues", [])
            gate_decision = review_json.get("gate_decision", "revise")

            critical_count = sum(
                1 for i in issues if i.get("severity") == "critical"
            )
            major_count = sum(
                1 for i in issues if i.get("severity") == "major"
            )

            logs.append(
                {
                    "iteration": iteration,
                    "phase": "review",
                    "critical": critical_count,
                    "major": major_count,
                    "decision": gate_decision,
                }
            )

            # --- stop condition ---
            if critical_count == 0 and gate_decision == "approve":
                return {
                    "ok": True,
                    "status": "completed",
                    "iterations": iteration,
                    "logs": logs,
                    "final_review": review_json,
                }

            # --- refine ---
            refine_result = refine_usecase.execute(
                repo_path=repo_path,
                review_json=review_json,
            )

            logs.append(
                {
                    "iteration": iteration,
                    "phase": "refine",
                    "write_path": refine_result["write_path"],
                }
            )

        # --- max iteration reached ---
        return {
            "ok": False,
            "status": "max_iterations_reached",
            "iterations": self.MAX_ITERATIONS,
            "logs": logs,
            "final_review": review_json,
        }
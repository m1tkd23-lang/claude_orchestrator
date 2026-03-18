# src\claude_orchestrator\core\workflow.py
from __future__ import annotations


def decide_next_from_report(role: str, report: dict, current_cycle: int, max_cycles: int) -> dict:
    if role == "implementer":
        status = str(report["status"])

        if status == "done":
            return {
                "status": "in_progress",
                "current_stage": "reviewer",
                "next_role": "reviewer",
                "last_completed_role": "implementer",
                "cycle": current_cycle,
            }

        if status in ("blocked", "need_input"):
            return {
                "status": "blocked",
                "current_stage": "implementer",
                "next_role": "none",
                "last_completed_role": "implementer",
                "cycle": current_cycle,
            }

        raise ValueError(f"Unsupported implementer status: {status}")

    if role == "reviewer":
        decision = str(report["decision"])

        if decision in ("ok", "needs_fix"):
            return {
                "status": "in_progress",
                "current_stage": "director",
                "next_role": "director",
                "last_completed_role": "reviewer",
                "cycle": current_cycle,
            }

        if decision == "blocked":
            return {
                "status": "blocked",
                "current_stage": "reviewer",
                "next_role": "none",
                "last_completed_role": "reviewer",
                "cycle": current_cycle,
            }

        raise ValueError(f"Unsupported reviewer decision: {decision}")

    if role == "director":
        final_action = str(report["final_action"])

        if final_action == "approve":
            return {
                "status": "completed",
                "current_stage": "director",
                "next_role": "none",
                "last_completed_role": "director",
                "cycle": current_cycle,
            }

        if final_action == "stop":
            return {
                "status": "stopped",
                "current_stage": "director",
                "next_role": "none",
                "last_completed_role": "director",
                "cycle": current_cycle,
            }

        if final_action == "revise":
            next_cycle = current_cycle + 1
            if next_cycle > max_cycles:
                return {
                    "status": "stopped",
                    "current_stage": "director",
                    "next_role": "none",
                    "last_completed_role": "director",
                    "cycle": current_cycle,
                }

            return {
                "status": "in_progress",
                "current_stage": "implementer",
                "next_role": "implementer",
                "last_completed_role": "director",
                "cycle": next_cycle,
            }

        raise ValueError(f"Unsupported director final_action: {final_action}")

    raise ValueError(f"Unsupported role: {role}")
# src\claude_orchestrator\gui\planner_helpers.py
from __future__ import annotations


def build_proposal_list_text(proposal: dict, state: str) -> str:
    proposal_id = str(proposal.get("proposal_id", ""))
    priority = str(proposal.get("priority", ""))
    title = str(proposal.get("title", ""))
    return f"{proposal_id} | state={state} | priority={priority} | title={title}"


def build_proposal_detail_text(proposal: dict, state: str) -> str:
    context_files = proposal.get("context_files", []) or []
    constraints = proposal.get("constraints", []) or []

    context_text = "\n".join(f"- {item}" for item in context_files) or "(none)"
    constraints_text = "\n".join(f"- {item}" for item in constraints) or "(none)"

    return (
        f"proposal_id: {proposal.get('proposal_id', '')}\n"
        f"state: {state}\n"
        f"priority: {proposal.get('priority', '')}\n"
        f"title: {proposal.get('title', '')}\n\n"
        f"description:\n{proposal.get('description', '')}\n\n"
        f"reason:\n{proposal.get('reason', '')}\n\n"
        f"context_files:\n{context_text}\n\n"
        f"constraints:\n{constraints_text}"
    )


def proposal_to_task_form_fields(proposal: dict) -> dict[str, str]:
    context_files = proposal.get("context_files", []) or []
    constraints = proposal.get("constraints", []) or []

    return {
        "title": str(proposal.get("title", "")).strip(),
        "description": str(proposal.get("description", "")).strip(),
        "context_files_text": "\n".join(str(item) for item in context_files if str(item).strip()),
        "constraints_text": "\n".join(str(item) for item in constraints if str(item).strip()),
    }
# src/claude_orchestrator/services/planning_context_compactor.py
from __future__ import annotations

from typing import Any


def compact_task_json_for_planning(task_json: dict[str, Any]) -> dict[str, Any]:
    return {
        "task_id": task_json.get("task_id", ""),
        "title": task_json.get("title", ""),
        "description": task_json.get("description", ""),
        "task_type": task_json.get("task_type", ""),
        "risk_level": task_json.get("risk_level", ""),
        "depends_on": _as_list(task_json.get("depends_on")),
        "context_files": _as_list(task_json.get("context_files")),
        "constraints": _as_list(task_json.get("constraints")),
        "acceptance_criteria": _as_list(task_json.get("acceptance_criteria")),
        "reference_docs": _as_list(task_json.get("reference_docs")),
        "notes": _as_list(task_json.get("notes")),
    }


def compact_state_json_for_planning(state_json: dict[str, Any]) -> dict[str, Any]:
    return {
        "status": state_json.get("status", ""),
        "current_stage": state_json.get("current_stage", ""),
        "next_role": state_json.get("next_role", ""),
        "cycle": state_json.get("cycle", 1),
        "revision": state_json.get("revision", 1),
        "last_completed_role": state_json.get("last_completed_role", ""),
        "max_cycles": state_json.get("max_cycles", 0),
    }


def compact_project_config_for_planning(
    project_config: dict[str, Any],
) -> dict[str, Any]:
    return {
        "development_mode": project_config.get("development_mode", ""),
        "orchestrator": _as_dict(project_config.get("orchestrator")),
        "planner": _as_dict(project_config.get("planner")),
    }


def compact_planner_report_for_plan_director(
    report_json: dict[str, Any],
) -> dict[str, Any]:
    proposals = report_json.get("proposals")
    compact_proposals = []
    if isinstance(proposals, list):
        for proposal in proposals:
            compact_proposals.append(_compact_planner_proposal(proposal))

    return {
        "role": report_json.get("role", ""),
        "source_task_id": report_json.get("source_task_id", ""),
        "cycle": report_json.get("cycle", 0),
        "summary": report_json.get("summary", ""),
        "proposals": compact_proposals,
    }


def compact_planner_state_for_plan_director(state_json: dict[str, Any]) -> dict[str, Any]:
    raw_states = state_json.get("proposal_states")
    proposal_states = []
    if isinstance(raw_states, list):
        for item in raw_states:
            if isinstance(item, dict):
                proposal_states.append(
                    {
                        "proposal_id": item.get("proposal_id", ""),
                        "state": item.get("state", "proposed"),
                    }
                )

    return {
        "source_task_id": state_json.get("source_task_id", ""),
        "cycle": state_json.get("cycle", 0),
        "proposal_states": proposal_states,
    }


def _compact_planner_proposal(proposal: Any) -> dict[str, Any]:
    if not isinstance(proposal, dict):
        return {
            "proposal_id": "",
            "planner_type": "",
            "proposal_kind": "",
            "title": "",
            "description": "",
            "why_now": "",
            "priority": "",
            "reason": "",
            "context_files": [],
            "constraints": [],
            "depends_on": [],
            "docs_update_plan": {},
        }

    return {
        "proposal_id": proposal.get("proposal_id", ""),
        "planner_type": proposal.get("planner_type", ""),
        "proposal_kind": proposal.get("proposal_kind", ""),
        "title": proposal.get("title", ""),
        "description": proposal.get("description", ""),
        "why_now": proposal.get("why_now", ""),
        "priority": proposal.get("priority", ""),
        "reason": proposal.get("reason", ""),
        "context_files": _as_list(proposal.get("context_files")),
        "constraints": _as_list(proposal.get("constraints")),
        "depends_on": _as_list(proposal.get("depends_on")),
        "docs_update_plan": _as_dict(proposal.get("docs_update_plan")),
    }


def _as_list(value: Any) -> list[Any]:
    if isinstance(value, list):
        return value
    return []


def _as_dict(value: Any) -> dict[str, Any]:
    if isinstance(value, dict):
        return value
    return {}

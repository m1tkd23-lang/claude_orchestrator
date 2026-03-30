# src\claude_orchestrator\services\planning_context_compactor.py
from __future__ import annotations

from typing import Any


_MAX_REFERENCE_DOC_EXCERPT_LINES = 12
_MAX_REFERENCE_DOC_EXCERPT_CHARS = 1200


def compact_task_json_for_planner(task_json: dict[str, Any]) -> dict[str, Any]:
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
        "docs_update_plan": _as_dict(task_json.get("docs_update_plan")),
    }


def compact_task_json_for_plan_director(task_json: dict[str, Any]) -> dict[str, Any]:
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
    }


def compact_task_json_for_planning(task_json: dict[str, Any]) -> dict[str, Any]:
    return compact_task_json_for_planner(task_json)


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


def compact_project_config_for_planner(
    project_config: dict[str, Any],
) -> dict[str, Any]:
    return {
        "development_mode": project_config.get("development_mode", ""),
        "orchestrator": _compact_config_section(project_config.get("orchestrator")),
        "planner": _compact_config_section(project_config.get("planner")),
    }


def compact_project_config_for_plan_director(
    project_config: dict[str, Any],
) -> dict[str, Any]:
    return {
        "development_mode": project_config.get("development_mode", ""),
        "planner": _compact_config_section(project_config.get("planner")),
    }


def compact_project_config_for_planning(
    project_config: dict[str, Any],
) -> dict[str, Any]:
    return compact_project_config_for_planner(project_config)


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


def compact_reference_doc_for_planner(
    relative_path: str,
    content: str,
) -> dict[str, Any]:
    excerpt_lines: list[str] = []
    heading_lines: list[str] = []
    excerpt_char_count = 0

    for raw_line in content.splitlines():
        line = raw_line.rstrip()
        if line.startswith("#") and len(heading_lines) < 6:
            heading_lines.append(line)

        if not line.strip():
            continue

        next_count = excerpt_char_count + len(line)
        if (
            len(excerpt_lines) >= _MAX_REFERENCE_DOC_EXCERPT_LINES
            or next_count > _MAX_REFERENCE_DOC_EXCERPT_CHARS
        ):
            break

        excerpt_lines.append(line)
        excerpt_char_count = next_count

    return {
        "path": relative_path,
        "status": "ok",
        "title": heading_lines[0] if heading_lines else "",
        "headings": heading_lines[:6],
        "excerpt": "\n".join(excerpt_lines),
        "line_count": len(content.splitlines()),
        "truncated": len(content.splitlines()) > len(excerpt_lines),
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


def _compact_config_section(value: Any) -> dict[str, Any]:
    if not isinstance(value, dict):
        return {}

    compact: dict[str, Any] = {}
    for key, raw in value.items():
        if _is_simple_value(raw):
            compact[key] = raw
            continue

        if isinstance(raw, list) and _is_simple_list(raw):
            compact[key] = raw[:8]
            if len(raw) > len(compact[key]):
                compact[f"{key}_truncated_count"] = len(raw) - len(compact[key])
            continue

        if isinstance(raw, dict):
            nested = {
                nested_key: nested_value
                for nested_key, nested_value in raw.items()
                if _is_simple_value(nested_value)
            }
            if nested:
                compact[key] = nested

    return compact


def _is_simple_value(value: Any) -> bool:
    return isinstance(value, (str, int, float, bool)) or value is None


def _is_simple_list(value: list[Any]) -> bool:
    return all(_is_simple_value(item) for item in value)


def _as_list(value: Any) -> list[Any]:
    if isinstance(value, list):
        return value
    return []


def _as_dict(value: Any) -> dict[str, Any]:
    if isinstance(value, dict):
        return value
    return {}
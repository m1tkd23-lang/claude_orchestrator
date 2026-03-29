# src/claude_orchestrator/services/context_compactor.py
from __future__ import annotations

from typing import Any


def build_implementer_context_for_reviewer(
    report_json: dict[str, Any],
) -> dict[str, Any]:
    """implementer report から reviewer 向け compact context を生成する."""

    return {
        "source_role": "implementer",
        "status": report_json.get("status", ""),
        "summary": report_json.get("summary", ""),
        "changed_files": _as_list(report_json.get("changed_files")),
        "commands_run": _as_list(report_json.get("commands_run")),
        "results": _as_list(report_json.get("results")),
        "risks": _as_list(report_json.get("risks")),
        "docs_update_result": _as_dict(report_json.get("docs_update_result")),
    }


def build_reviewer_context_for_director(
    report_json: dict[str, Any],
) -> dict[str, Any]:
    """reviewer report から director 向け compact context を生成する."""

    context: dict[str, Any] = {
        "source_role": "reviewer",
        "decision": report_json.get("decision", ""),
        "summary": report_json.get("summary", ""),
        "must_fix": _as_list(report_json.get("must_fix")),
        "risks": _as_list(report_json.get("risks")),
        "docs_review_result": _as_dict(report_json.get("docs_review_result")),
    }

    nice_to_have = _as_list(report_json.get("nice_to_have"))
    if nice_to_have:
        context["nice_to_have"] = nice_to_have

    return context


def build_director_context_for_next_role(
    report_json: dict[str, Any],
) -> dict[str, Any]:
    """director report から次 role 向け compact context を生成する."""

    return {
        "source_role": "director",
        "final_action": report_json.get("final_action", ""),
        "summary": report_json.get("summary", ""),
        "next_actions": _as_list(report_json.get("next_actions")),
        "remaining_risks": _as_list(report_json.get("remaining_risks")),
        "docs_decision": _as_dict(report_json.get("docs_decision")),
    }


def _as_list(value: Any) -> list[Any]:
    if isinstance(value, list):
        return value
    return []


def _as_dict(value: Any) -> dict[str, Any]:
    if isinstance(value, dict):
        return value
    return {}
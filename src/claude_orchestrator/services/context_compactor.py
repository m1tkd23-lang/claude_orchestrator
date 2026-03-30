# src\claude_orchestrator\services\context_compactor.py
from __future__ import annotations

from typing import Any


_MAX_RESULTS_COUNT = 6
_MAX_TEST_FILES_SAMPLE = 5
_MAX_STRING_LENGTH = 240


def build_implementer_context_for_reviewer(
    report_json: dict[str, Any],
) -> dict[str, Any]:
    """implementer report から reviewer / director 向け compact context を生成する."""

    compact_results, compact_meta = _compact_results_for_handoff(
        report_json.get("results")
    )

    return {
        "source_role": "implementer",
        "status": report_json.get("status", ""),
        "summary": report_json.get("summary", ""),
        "changed_files": _as_list(report_json.get("changed_files")),
        "commands_run": _as_list(report_json.get("commands_run")),
        "results": compact_results,
        "results_compact_meta": compact_meta,
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


def compact_task_json_for_execution_role(
    role: str,
    task_json: dict[str, Any],
) -> dict[str, Any]:
    """execution 系 role 向けに task.json を compact 化する."""

    base = {
        "task_id": task_json.get("task_id", ""),
        "title": task_json.get("title", ""),
        "description": task_json.get("description", ""),
        "task_type": task_json.get("task_type", ""),
        "risk_level": task_json.get("risk_level", ""),
        "context_files": _as_list(task_json.get("context_files")),
        "constraints": _as_list(task_json.get("constraints")),
    }

    if role == "implementer":
        base["assigned_role_skills"] = _extract_role_skills(task_json, "implementer")
        base["skill_selection_reason"] = task_json.get("skill_selection_reason", "")
        base["initial_execution_notes"] = task_json.get("initial_execution_notes", "")
        acceptance_criteria = _as_list(task_json.get("acceptance_criteria"))
        if acceptance_criteria:
            base["acceptance_criteria"] = acceptance_criteria
        reference_docs = _as_list(task_json.get("reference_docs"))
        if reference_docs:
            base["reference_docs"] = reference_docs
        notes = _as_list(task_json.get("notes"))
        if notes:
            base["notes"] = notes
        return base

    if role == "reviewer":
        acceptance_criteria = _as_list(task_json.get("acceptance_criteria"))
        if acceptance_criteria:
            base["acceptance_criteria"] = acceptance_criteria
        return base

    if role == "director":
        acceptance_criteria = _as_list(task_json.get("acceptance_criteria"))
        if acceptance_criteria:
            base["acceptance_criteria"] = acceptance_criteria
        depends_on = _as_list(task_json.get("depends_on"))
        if depends_on:
            base["depends_on"] = depends_on
        return base

    return task_json


def _compact_results_for_handoff(
    value: Any,
) -> tuple[list[dict[str, Any]], dict[str, int]]:
    raw_results = _as_list(value)
    compact_results: list[dict[str, Any]] = []

    for raw in raw_results[:_MAX_RESULTS_COUNT]:
        compact_results.append(_compact_result_item(raw))

    return (
        compact_results,
        {
            "total_count": len(raw_results),
            "included_count": len(compact_results),
            "omitted_count": max(0, len(raw_results) - len(compact_results)),
        },
    )


def _compact_result_item(value: Any) -> dict[str, Any]:
    if not isinstance(value, dict):
        return {"summary": _truncate_string(str(value))}

    compact: dict[str, Any] = {}

    preferred_scalar_keys = [
        "kind",
        "status",
        "target",
        "command",
        "summary",
        "message",
        "duration_seconds",
        "returncode",
        "passed",
        "failed",
        "errors",
        "warnings",
        "count",
    ]
    for key in preferred_scalar_keys:
        if key in value and _is_simple_json_value(value[key]):
            compact[key] = _truncate_value(value[key])

    test_files = value.get("test_files")
    if isinstance(test_files, list):
        compact["test_files_sample"] = test_files[:_MAX_TEST_FILES_SAMPLE]
        compact["test_files_truncated_count"] = max(
            0,
            len(test_files) - len(compact["test_files_sample"]),
        )

    simple_list_keys = ["artifacts", "updated_files", "checked_files"]
    for key in simple_list_keys:
        raw_list = value.get(key)
        if isinstance(raw_list, list) and raw_list:
            compact[key] = raw_list[:5]
            if len(raw_list) > len(compact[key]):
                compact[f"{key}_truncated_count"] = len(raw_list) - len(compact[key])

    if not compact:
        for key, raw in value.items():
            if _is_simple_json_value(raw):
                compact[key] = _truncate_value(raw)
            if len(compact) >= 6:
                break

    return compact


def _extract_role_skills(task_json: dict[str, Any], role: str) -> list[Any]:
    role_skill_plan = task_json.get("role_skill_plan")
    if not isinstance(role_skill_plan, dict):
        return []
    return _as_list(role_skill_plan.get(role))


def _truncate_value(value: Any) -> Any:
    if isinstance(value, str):
        return _truncate_string(value)
    return value


def _truncate_string(value: str) -> str:
    if len(value) <= _MAX_STRING_LENGTH:
        return value
    return value[: _MAX_STRING_LENGTH - 3] + "..."


def _is_simple_json_value(value: Any) -> bool:
    return isinstance(value, (str, int, float, bool)) or value is None


def _as_list(value: Any) -> list[Any]:
    if isinstance(value, list):
        return value
    return []


def _as_dict(value: Any) -> dict[str, Any]:
    if isinstance(value, dict):
        return value
    return {}
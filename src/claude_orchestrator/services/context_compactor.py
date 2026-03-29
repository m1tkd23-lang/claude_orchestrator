# src/claude_orchestrator/services/context_compactor.py
from __future__ import annotations

from typing import Any


def build_implementer_context_for_reviewer(
    report_json: dict[str, Any],
) -> dict[str, Any]:
    """implementer report から reviewer 向け compact context を生成する."""
    compact_results = _compact_results(_as_list(report_json.get("results")))

    return {
        "source_role": "implementer",
        "status": report_json.get("status", ""),
        "summary": report_json.get("summary", ""),
        "changed_files": _as_list(report_json.get("changed_files")),
        "commands_run": _as_list(report_json.get("commands_run")),
        "results": compact_results["results"],
        "results_compact": compact_results["results"],
        "results_compact_meta": compact_results["meta"],
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


def _compact_results(
    raw_results: list[Any],
    *,
    max_results: int = 8,
    max_list_items: int = 6,
    max_test_files: int = 4,
) -> dict[str, Any]:
    compact_items = [
        _compact_result_item(
            item,
            max_list_items=max_list_items,
            max_test_files=max_test_files,
        )
        for item in raw_results[:max_results]
    ]
    total_count = len(raw_results)
    included_count = len(compact_items)
    omitted_count = max(total_count - included_count, 0)

    return {
        "results": compact_items,
        "meta": {
            "total_count": total_count,
            "included_count": included_count,
            "omitted_count": omitted_count,
            "max_results": max_results,
            "max_list_items": max_list_items,
            "max_test_files": max_test_files,
        },
    }


def _compact_result_item(
    item: Any,
    *,
    max_list_items: int,
    max_test_files: int,
) -> Any:
    if isinstance(item, dict):
        compact: dict[str, Any] = {}
        for key, value in item.items():
            if isinstance(value, list):
                if key == "test_files":
                    compact[key] = value[:max_test_files]
                    compact["test_files_truncated_count"] = max(
                        len(value) - len(compact[key]),
                        0,
                    )
                else:
                    compact[key] = value[:max_list_items]
                    compact[f"{key}_truncated_count"] = max(
                        len(value) - len(compact[key]),
                        0,
                    )
                continue

            if isinstance(value, dict):
                compact[key] = _compact_result_nested_dict(
                    value,
                    max_list_items=max_list_items,
                )
                continue

            compact[key] = value

        return compact

    if isinstance(item, list):
        return item[:max_list_items]

    return item


def _compact_result_nested_dict(
    payload: dict[str, Any],
    *,
    max_list_items: int,
) -> dict[str, Any]:
    compact: dict[str, Any] = {}
    for key, value in payload.items():
        if isinstance(value, list):
            compact[key] = value[:max_list_items]
            compact[f"{key}_truncated_count"] = max(
                len(value) - len(compact[key]),
                0,
            )
            continue

        if isinstance(value, dict):
            compact[key] = list(value.keys())[:max_list_items]
            compact[f"{key}_key_count"] = len(value)
            continue

        compact[key] = value

    return compact

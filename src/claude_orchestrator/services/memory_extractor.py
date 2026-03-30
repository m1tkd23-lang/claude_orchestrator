# src\claude_orchestrator\services\memory_extractor.py
from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path
import re

from claude_orchestrator.infrastructure.memory.memory_models import (
    IMPORTANCE_HIGH,
    IMPORTANCE_MEDIUM,
    ISSUE_TYPE_DECISION_REVISE,
    ISSUE_TYPE_DECISION_STOP,
    ISSUE_TYPE_DOCS_CONSISTENCY_ISSUE,
    ISSUE_TYPE_DOCS_UPDATE_MISSING,
    ISSUE_TYPE_FILE_SCOPE_MISMATCH,
    ISSUE_TYPE_IMPLEMENTATION_BLOCKED,
    ISSUE_TYPE_REVIEW_BLOCKED,
    ISSUE_TYPE_REVIEW_FINDINGS,
    ISSUE_TYPE_TEST_FAILURE,
    ISSUE_TYPE_UNKNOWN_ISSUE,
    MEMORY_KIND_EXECUTION_ISSUE,
    MemoryRecord,
)


def extract_memory_record(
    *,
    memory_id: str,
    task_id: str,
    role: str,
    cycle: int,
    revision: int,
    development_mode: str,
    task_json: dict,
    state_json: dict,
    report_json: dict,
    source_report_path: str,
) -> MemoryRecord | None:
    if not _is_target_report(role=role, report_json=report_json):
        return None

    issue_type = _detect_issue_type(role=role, report_json=report_json)
    importance = _detect_importance(role=role, report_json=report_json)
    summary = _extract_summary(report_json)
    related_files = _extract_related_files(task_json=task_json, report_json=report_json)
    trigger_conditions = _extract_trigger_conditions(
        role=role,
        task_json=task_json,
        state_json=state_json,
        report_json=report_json,
    )
    recommended_action = _extract_recommended_action(role=role, report_json=report_json)
    avoid_action = _extract_avoid_action(role=role, report_json=report_json)
    evidence = _build_evidence(role=role, report_json=report_json)

    now_text = _current_timestamp_text()

    return MemoryRecord(
        memory_id=memory_id,
        memory_kind=MEMORY_KIND_EXECUTION_ISSUE,
        source_task_id=task_id,
        source_role=role,
        source_cycle=cycle,
        source_revision=revision,
        development_mode=development_mode,
        issue_type=issue_type,
        importance=importance,
        summary=summary,
        trigger_conditions=trigger_conditions,
        recommended_action=recommended_action,
        avoid_action=avoid_action,
        related_files=related_files,
        evidence=evidence,
        source_report_path=source_report_path,
        created_at=now_text,
        updated_at=now_text,
    )


def _is_target_report(*, role: str, report_json: dict) -> bool:
    if role == "implementer":
        return str(report_json.get("status", "")).strip() == "blocked"

    if role == "reviewer":
        decision = str(report_json.get("decision", "")).strip()
        return decision in {"needs_fix", "blocked"}

    if role == "director":
        final_action = str(report_json.get("final_action", "")).strip()
        return final_action in {"revise", "stop"}

    return False


def _detect_issue_type(*, role: str, report_json: dict) -> str:
    summary_text = _joined_text(
        [
            report_json.get("summary", ""),
            *_as_list(report_json.get("risks")),
            *_as_list(report_json.get("must_fix")),
            *_as_list(report_json.get("next_actions")),
        ]
    ).lower()

    if role == "implementer":
        if _contains_any(summary_text, ["pytest", "test", "失敗", "error", "failed"]):
            return ISSUE_TYPE_TEST_FAILURE

        docs_update_result = report_json.get("docs_update_result")
        if isinstance(docs_update_result, dict):
            reason_text = _joined_text(
                [
                    docs_update_result.get("reason", ""),
                    *_as_list(docs_update_result.get("updated_files")),
                ]
            ).lower()
            if _contains_any(reason_text, ["docs", "doc", "仕様", "記録", "inventory"]):
                return ISSUE_TYPE_DOCS_UPDATE_MISSING

        if _contains_any(
            summary_text,
            ["対象ファイル", "影響範囲", "関連ファイル", "不足", "未反映"],
        ):
            return ISSUE_TYPE_FILE_SCOPE_MISMATCH

        return ISSUE_TYPE_IMPLEMENTATION_BLOCKED

    if role == "reviewer":
        if str(report_json.get("decision", "")).strip() == "blocked":
            return ISSUE_TYPE_REVIEW_BLOCKED

        docs_review_result = report_json.get("docs_review_result")
        if isinstance(docs_review_result, dict):
            docs_text = _joined_text(
                [
                    docs_review_result.get("reason", ""),
                    *_as_list(docs_review_result.get("target_files")),
                ]
            ).lower()
            if _contains_any(docs_text, ["docs", "doc", "仕様", "整合", "inventory"]):
                return ISSUE_TYPE_DOCS_CONSISTENCY_ISSUE

        if _contains_any(
            summary_text,
            ["docs", "doc", "仕様", "整合", "記録", "inventory"],
        ):
            return ISSUE_TYPE_DOCS_CONSISTENCY_ISSUE

        return ISSUE_TYPE_REVIEW_FINDINGS

    if role == "director":
        final_action = str(report_json.get("final_action", "")).strip()
        if final_action == "stop":
            return ISSUE_TYPE_DECISION_STOP
        if final_action == "revise":
            return ISSUE_TYPE_DECISION_REVISE

    return ISSUE_TYPE_UNKNOWN_ISSUE


def _detect_importance(*, role: str, report_json: dict) -> str:
    if role == "director":
        final_action = str(report_json.get("final_action", "")).strip()
        if final_action in {"revise", "stop"}:
            return IMPORTANCE_HIGH

    if role == "reviewer":
        decision = str(report_json.get("decision", "")).strip()
        if decision == "blocked":
            return IMPORTANCE_HIGH
        if decision == "needs_fix":
            return IMPORTANCE_MEDIUM

    if role == "implementer":
        status = str(report_json.get("status", "")).strip()
        if status == "blocked":
            return IMPORTANCE_HIGH

    return IMPORTANCE_MEDIUM


def _extract_summary(report_json: dict) -> str:
    summary = str(report_json.get("summary", "")).strip()
    if summary:
        return summary
    return "(summary unavailable)"


def _extract_related_files(*, task_json: dict, report_json: dict) -> list[str]:
    candidates: list[str] = []

    for path in _as_list(task_json.get("context_files")):
        normalized = _normalize_path_like(path)
        if normalized:
            candidates.append(normalized)

    for path in _as_list(report_json.get("changed_files")):
        normalized = _normalize_path_like(path)
        if normalized:
            candidates.append(normalized)

    text_sources = [
        str(report_json.get("summary", "")),
        *_as_list(report_json.get("must_fix")),
        *_as_list(report_json.get("next_actions")),
        *_as_list(report_json.get("risks")),
    ]
    for text in text_sources:
        for path in _extract_paths_from_text(text):
            candidates.append(path)

    return _unique_preserve_order(candidates)


def _extract_trigger_conditions(
    *,
    role: str,
    task_json: dict,
    state_json: dict,
    report_json: dict,
) -> list[str]:
    conditions: list[str] = []

    task_type = str(task_json.get("task_type", "")).strip()
    if task_type:
        conditions.append(f"task_type:{task_type}")

    current_stage = str(state_json.get("current_stage", "")).strip()
    if current_stage:
        conditions.append(f"stage:{current_stage}")

    for path in _as_list(task_json.get("context_files"))[:3]:
        normalized = _normalize_path_like(path)
        if normalized:
            conditions.append(f"context_file:{normalized}")

    if role == "implementer":
        for risk in _as_list(report_json.get("risks"))[:3]:
            text = str(risk).strip()
            if text:
                conditions.append(text)

    if role == "reviewer":
        for item in _as_list(report_json.get("must_fix"))[:3]:
            text = str(item).strip()
            if text:
                conditions.append(text)

    if role == "director":
        for item in _as_list(report_json.get("remaining_risks"))[:3]:
            text = str(item).strip()
            if text:
                conditions.append(text)

    return _unique_preserve_order(conditions)


def _extract_recommended_action(*, role: str, report_json: dict) -> list[str]:
    if role == "implementer":
        actions = _as_list(report_json.get("results"))
        normalized = [_normalize_result_like(item) for item in actions]
        return _unique_preserve_order([x for x in normalized if x])

    if role == "reviewer":
        return _unique_preserve_order(
            [str(x).strip() for x in _as_list(report_json.get("must_fix")) if str(x).strip()]
        )

    if role == "director":
        return _unique_preserve_order(
            [str(x).strip() for x in _as_list(report_json.get("next_actions")) if str(x).strip()]
        )

    return []


def _extract_avoid_action(*, role: str, report_json: dict) -> list[str]:
    if role == "implementer":
        values = _as_list(report_json.get("risks"))
    elif role == "reviewer":
        values = _as_list(report_json.get("risks"))
    elif role == "director":
        values = _as_list(report_json.get("remaining_risks"))
    else:
        values = []

    return _unique_preserve_order([str(x).strip() for x in values if str(x).strip()])


def _build_evidence(*, role: str, report_json: dict) -> dict:
    evidence: dict[str, object] = {
        "role": role,
    }

    if role == "implementer":
        evidence["status"] = str(report_json.get("status", "")).strip()
        evidence["changed_files_count"] = len(_as_list(report_json.get("changed_files")))
        evidence["results_count"] = len(_as_list(report_json.get("results")))
        evidence["risks_count"] = len(_as_list(report_json.get("risks")))
        return evidence

    if role == "reviewer":
        evidence["decision"] = str(report_json.get("decision", "")).strip()
        evidence["must_fix_count"] = len(_as_list(report_json.get("must_fix")))
        evidence["risks_count"] = len(_as_list(report_json.get("risks")))
        return evidence

    if role == "director":
        evidence["final_action"] = str(report_json.get("final_action", "")).strip()
        evidence["next_actions_count"] = len(_as_list(report_json.get("next_actions")))
        evidence["remaining_risks_count"] = len(
            _as_list(report_json.get("remaining_risks"))
        )
        return evidence

    return evidence


def _normalize_result_like(value: object) -> str:
    if isinstance(value, dict):
        pieces: list[str] = []
        for key in ("kind", "status", "summary", "message", "command", "target"):
            raw = value.get(key)
            if raw is None:
                continue
            text = str(raw).strip()
            if text:
                pieces.append(f"{key}={text}")
        if pieces:
            return "; ".join(pieces)

    text = str(value).strip()
    return text


def _extract_paths_from_text(text: str) -> list[str]:
    matches = re.findall(
        r"(?:[A-Za-z]:)?[\\/][^\\/\s]+(?:[\\/][^\\/\s]+)+|(?:src|apps|docs)[\\/][^\\/\s]+(?:[\\/][^\\/\s]+)+",
        text,
    )
    normalized: list[str] = []
    for match in matches:
        path = _normalize_path_like(match)
        if path:
            normalized.append(path)
    return normalized


def _normalize_path_like(value: object) -> str:
    text = str(value).strip().replace("\\", "/")
    if not text:
        return ""
    return text


def _contains_any(text: str, needles: list[str]) -> bool:
    return any(needle.lower() in text for needle in needles)


def _joined_text(values: list[object]) -> str:
    parts: list[str] = []
    for value in values:
        text = str(value).strip()
        if text:
            parts.append(text)
    return "\n".join(parts)


def _as_list(value: object) -> list:
    if isinstance(value, list):
        return value
    return []


def _unique_preserve_order(values: list[str]) -> list[str]:
    seen: set[str] = set()
    result: list[str] = []
    for value in values:
        normalized = value.strip()
        if not normalized:
            continue
        if normalized in seen:
            continue
        seen.add(normalized)
        result.append(normalized)
    return result


def _current_timestamp_text() -> str:
    return (
        datetime.now(timezone.utc)
        .replace(microsecond=0)
        .isoformat()
        .replace("+00:00", "Z")
    )
# src\claude_orchestrator\services\memory_scoring.py
from __future__ import annotations

from pathlib import PurePath
import re

from claude_orchestrator.infrastructure.memory.memory_models import (
    IMPORTANCE_HIGH,
    IMPORTANCE_MEDIUM,
    MemoryRecord,
    MemorySearchContext,
)


def rank_memory_records(
    *,
    context: MemorySearchContext,
    records: list[MemoryRecord],
) -> list[tuple[MemoryRecord, float]]:
    scored: list[tuple[MemoryRecord, float]] = []

    for record in records:
        score = score_record(context=context, record=record)
        scored.append((record, score))

    scored.sort(
        key=lambda item: (
            item[1],
            extract_task_number(item[0].source_task_id) or -1,
            item[0].created_at,
            item[0].memory_id,
        ),
        reverse=True,
    )
    return scored


def score_record(
    *,
    context: MemorySearchContext,
    record: MemoryRecord,
) -> float:
    score = 0.0
    score += _score_related_files(context=context, record=record)
    score += _score_issue_type(context=context, record=record)
    score += _score_role_affinity(context=context, record=record)
    score += _score_importance(record=record)
    score += _score_task_proximity(
        current_task_id=context.task_id,
        source_task_id=record.source_task_id,
    )
    return score


def extract_task_number(task_id: str) -> int | None:
    match = re.search(r"TASK-(\d+)", str(task_id).strip(), re.IGNORECASE)
    if not match:
        return None
    return int(match.group(1))


def score_task_proximity(
    current_task_id: str,
    source_task_id: str,
) -> float:
    current_num = extract_task_number(current_task_id)
    source_num = extract_task_number(source_task_id)

    if current_num is None or source_num is None:
        return 0.0

    diff = abs(current_num - source_num)
    if diff <= 10:
        return 1.0
    return 0.5


def _score_related_files(
    *,
    context: MemorySearchContext,
    record: MemoryRecord,
) -> float:
    if not context.context_files or not record.related_files:
        return 0.0

    current_full = {_normalize_path(path) for path in context.context_files if path}
    current_base = {
        _basename(path)
        for path in context.context_files
        if _basename(path)
    }

    score = 0.0
    for related in record.related_files:
        normalized = _normalize_path(related)
        if not normalized:
            continue

        if normalized in current_full:
            score += 4.0
            continue

        base = _basename(normalized)
        if base and base in current_base:
            score += 2.0

    return score


def _score_issue_type(
    *,
    context: MemorySearchContext,
    record: MemoryRecord,
) -> float:
    if not context.issue_type_hints:
        return 0.0

    issue_hints = {str(x).strip() for x in context.issue_type_hints if str(x).strip()}
    if record.issue_type in issue_hints:
        return 3.0
    return 0.0


def _score_role_affinity(
    *,
    context: MemorySearchContext,
    record: MemoryRecord,
) -> float:
    role = context.role
    source_role = record.source_role

    if role == "implementer":
        if source_role == "implementer":
            return 2.0
        if source_role == "reviewer":
            return 2.0
        if source_role == "director":
            return 1.0
        return 0.0

    if role == "task_router":
        if source_role == "director":
            return 2.0
        if source_role == "reviewer":
            return 2.0
        if source_role == "implementer":
            return 1.0
        return 0.0

    return 0.0


def _score_importance(*, record: MemoryRecord) -> float:
    if record.importance == IMPORTANCE_HIGH:
        return 2.0
    if record.importance == IMPORTANCE_MEDIUM:
        return 1.0
    return 0.0


def _normalize_path(path: str) -> str:
    return str(path).strip().replace("\\", "/")


def _basename(path: str) -> str:
    normalized = _normalize_path(path)
    if not normalized:
        return ""
    return PurePath(normalized).name
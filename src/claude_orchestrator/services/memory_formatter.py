# src\claude_orchestrator\services\memory_formatter.py
from __future__ import annotations

from claude_orchestrator.infrastructure.memory.memory_models import MemoryRecord


_MAX_TRIGGER_COUNT = 2
_MAX_ACTION_COUNT = 2
_MAX_TEXT_LENGTH = 120


def format_records_for_prompt(records: list[MemoryRecord]) -> str:
    if not records:
        return ""

    blocks = [_format_record(record) for record in records]
    return "\n\n".join(blocks).strip()


def _format_record(record: MemoryRecord) -> str:
    trigger = " / ".join(record.trigger_conditions[:_MAX_TRIGGER_COUNT]) or "条件情報なし"
    caution = _shorten(record.summary)
    action = " / ".join(record.recommended_action[:_MAX_ACTION_COUNT]) or "要確認"
    evidence = f"{record.source_task_id} / {record.source_role}"

    return (
        f"- 条件: {trigger}\n"
        f"  注意: {caution}\n"
        f"  推奨: {action}\n"
        f"  根拠: {evidence}"
    )


def _shorten(text: str) -> str:
    normalized = str(text).strip()
    if len(normalized) <= _MAX_TEXT_LENGTH:
        return normalized
    return normalized[: _MAX_TEXT_LENGTH - 3] + "..."
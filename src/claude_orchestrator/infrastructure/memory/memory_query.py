# src\claude_orchestrator\infrastructure\memory\memory_query.py
from __future__ import annotations

from dataclasses import dataclass, field


@dataclass(slots=True)
class MemoryQuery:
    memory_kind: str
    development_mode: str
    allowed_roles: list[str] = field(default_factory=list)
    allowed_issue_types: list[str] = field(default_factory=list)
    allowed_importance: list[str] = field(default_factory=list)
    limit: int = 50
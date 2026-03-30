# src\claude_orchestrator\infrastructure\memory\memory_models.py
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


MEMORY_KIND_EXECUTION_ISSUE = "execution_issue"

ISSUE_TYPE_IMPLEMENTATION_BLOCKED = "implementation_blocked"
ISSUE_TYPE_TEST_FAILURE = "test_failure"
ISSUE_TYPE_FILE_SCOPE_MISMATCH = "file_scope_mismatch"
ISSUE_TYPE_DOCS_UPDATE_MISSING = "docs_update_missing"
ISSUE_TYPE_REVIEW_FINDINGS = "review_findings"
ISSUE_TYPE_REVIEW_BLOCKED = "review_blocked"
ISSUE_TYPE_DOCS_CONSISTENCY_ISSUE = "docs_consistency_issue"
ISSUE_TYPE_DECISION_REVISE = "decision_revise"
ISSUE_TYPE_DECISION_STOP = "decision_stop"
ISSUE_TYPE_COMPLETION_NOT_MET = "completion_not_met"
ISSUE_TYPE_UNKNOWN_ISSUE = "unknown_issue"

IMPORTANCE_HIGH = "high"
IMPORTANCE_MEDIUM = "medium"


@dataclass(slots=True)
class MemoryRecord:
    memory_id: str
    memory_kind: str
    source_task_id: str
    source_role: str
    source_cycle: int
    source_revision: int
    development_mode: str

    issue_type: str
    importance: str

    summary: str
    trigger_conditions: list[str] = field(default_factory=list)
    recommended_action: list[str] = field(default_factory=list)
    avoid_action: list[str] = field(default_factory=list)
    related_files: list[str] = field(default_factory=list)
    evidence: dict[str, Any] = field(default_factory=dict)
    source_report_path: str = ""

    created_at: str = ""
    updated_at: str = ""


@dataclass(slots=True)
class MemorySearchContext:
    role: str
    task_id: str
    task_number: int | None
    development_mode: str
    context_files: list[str] = field(default_factory=list)
    issue_type_hints: list[str] = field(default_factory=list)
    max_results: int = 3
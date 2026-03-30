# src\claude_orchestrator\application\usecases\retrieve_memory_for_prompt_usecase.py
from __future__ import annotations

from pathlib import Path

from claude_orchestrator.infrastructure.memory.memory_models import (
    IMPORTANCE_HIGH,
    IMPORTANCE_MEDIUM,
    MEMORY_KIND_EXECUTION_ISSUE,
    MemorySearchContext,
)
from claude_orchestrator.infrastructure.memory.memory_query import MemoryQuery
from claude_orchestrator.infrastructure.memory.memory_store import MemoryStore
from claude_orchestrator.services.memory_formatter import format_records_for_prompt
from claude_orchestrator.services.memory_scoring import (
    extract_task_number,
    rank_memory_records,
)


class RetrieveMemoryForPromptUseCase:
    MAX_RESULTS = 3
    MIN_SCORE = 5.0

    def execute(
        self,
        *,
        repo_path: str,
        role: str,
        task_json: dict,
        state_json: dict,
        development_mode: str,
    ) -> dict:
        if role not in {"task_router", "implementer"}:
            return {
                "records": [],
                "recalled_notes_text": "",
            }

        target_repo = Path(repo_path).resolve()
        db_path = (
            target_repo
            / ".claude_orchestrator"
            / "runtime"
            / "context_memory.sqlite3"
        )
        if not db_path.exists():
            return {
                "records": [],
                "recalled_notes_text": "",
            }

        context = self._build_search_context(
            role=role,
            task_json=task_json,
            state_json=state_json,
            development_mode=development_mode,
        )
        query = self._build_query(role=role, development_mode=development_mode)

        store = MemoryStore(db_path)
        candidates = store.search_candidates(query)
        ranked = rank_memory_records(context=context, records=candidates)

        selected_records = [
            record
            for record, score in ranked
            if score >= self.MIN_SCORE
        ][: self.MAX_RESULTS]

        return {
            "records": selected_records,
            "recalled_notes_text": format_records_for_prompt(selected_records),
        }

    def _build_search_context(
        self,
        *,
        role: str,
        task_json: dict,
        state_json: dict,
        development_mode: str,
    ) -> MemorySearchContext:
        task_id = str(task_json.get("task_id", "")).strip()
        context_files = [
            str(path).strip()
            for path in task_json.get("context_files", [])
            if str(path).strip()
        ]

        issue_type_hints = self._detect_issue_type_hints(
            role=role,
            task_json=task_json,
            state_json=state_json,
        )

        return MemorySearchContext(
            role=role,
            task_id=task_id,
            task_number=extract_task_number(task_id),
            development_mode=development_mode,
            context_files=context_files,
            issue_type_hints=issue_type_hints,
            max_results=self.MAX_RESULTS,
        )

    def _build_query(
        self,
        *,
        role: str,
        development_mode: str,
    ) -> MemoryQuery:
        if role == "implementer":
            allowed_roles = ["implementer", "reviewer", "director"]
        else:
            allowed_roles = ["implementer", "reviewer", "director"]

        return MemoryQuery(
            memory_kind=MEMORY_KIND_EXECUTION_ISSUE,
            development_mode=development_mode,
            allowed_roles=allowed_roles,
            allowed_issue_types=[],
            allowed_importance=[IMPORTANCE_HIGH, IMPORTANCE_MEDIUM],
            limit=50,
        )

    @staticmethod
    def _detect_issue_type_hints(
        *,
        role: str,
        task_json: dict,
        state_json: dict,
    ) -> list[str]:
        hints: list[str] = []

        joined_text = "\n".join(
            [
                str(task_json.get("description", "")),
                *[str(x) for x in task_json.get("constraints", [])],
                *[str(x) for x in task_json.get("context_files", [])],
                str(state_json.get("current_stage", "")),
            ]
        ).lower()

        if any(token in joined_text for token in ["docs", "doc", "仕様", "inventory"]):
            hints.append("docs_update_missing")
            hints.append("docs_consistency_issue")

        if any(token in joined_text for token in ["test", "pytest", "テスト"]):
            hints.append("test_failure")

        if any(
            token in joined_text
            for token in ["影響範囲", "関連ファイル", "対象ファイル", "未反映"]
        ):
            hints.append("file_scope_mismatch")

        if role == "task_router":
            hints.append("decision_revise")
            hints.append("review_findings")

        if role == "implementer":
            hints.append("implementation_blocked")
            hints.append("review_findings")
            hints.append("decision_revise")

        # 順序維持ユニーク化
        result: list[str] = []
        seen: set[str] = set()
        for hint in hints:
            if hint in seen:
                continue
            seen.add(hint)
            result.append(hint)
        return result
# src\claude_orchestrator\infrastructure\requirements_runtime.py
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
import json
from typing import Any

from claude_orchestrator.infrastructure.requirements_paths import RequirementsPaths


@dataclass
class RequirementsWriteResult:
    path: str
    updated_at: str


class RequirementsRuntime:
    """requirements.json と関連ファイルの読込・保存を扱う."""

    def __init__(self, repo_root: str | Path) -> None:
        self.paths = RequirementsPaths(Path(repo_root).resolve())

    def load_requirements_json(self) -> dict[str, Any]:
        return self._load_json_file(self.paths.requirements_json)

    def save_requirements_json(
        self,
        requirements_json: dict[str, Any],
        *,
        changed_by: str = "system",
        change_summary: str | None = None,
        change_details: list[str] | None = None,
    ) -> RequirementsWriteResult:
        self.paths.ensure_directories()
        self._write_json_file(
            self.paths.requirements_json,
            requirements_json,
        )

        updated_at = _utc_now_iso()

        if change_summary:
            self.append_change_history(
                changed_by=changed_by,
                summary=change_summary,
                details=change_details or [],
                changed_at=updated_at,
            )

        return RequirementsWriteResult(
            path=str(self.paths.requirements_json),
            updated_at=updated_at,
        )

    def load_change_log_json(self) -> dict[str, Any]:
        return self._load_json_file(
            self.paths.requirements_change_log_json,
            fallback={"changes": []},
        )

    def append_change_history(
        self,
        *,
        changed_by: str,
        summary: str,
        details: list[str] | None = None,
        changed_at: str | None = None,
    ) -> None:
        payload = self.load_change_log_json()
        changes = payload.get("changes")
        if not isinstance(changes, list):
            changes = []

        changes.append(
            {
                "changed_at": changed_at or _utc_now_iso(),
                "changed_by": changed_by,
                "summary": summary,
                "details": list(details or []),
            }
        )
        payload["changes"] = changes
        self._write_json_file(self.paths.requirements_change_log_json, payload)

    def load_open_questions_json(self) -> dict[str, Any]:
        return self._load_json_file(
            self.paths.open_questions_json,
            fallback={"questions": []},
        )

    def save_open_questions_json(self, payload: dict[str, Any]) -> RequirementsWriteResult:
        self.paths.ensure_directories()
        self._write_json_file(self.paths.open_questions_json, payload)
        return RequirementsWriteResult(
            path=str(self.paths.open_questions_json),
            updated_at=_utc_now_iso(),
        )

    def write_generated_docs(self, docs: dict[str, str]) -> list[RequirementsWriteResult]:
        self.paths.ensure_directories()

        results: list[RequirementsWriteResult] = []
        for relative_path, content in docs.items():
            target_path = self.paths.repo_root / relative_path
            target_path.parent.mkdir(parents=True, exist_ok=True)
            target_path.write_text(content, encoding="utf-8")
            results.append(
                RequirementsWriteResult(
                    path=str(target_path),
                    updated_at=_utc_now_iso(),
                )
            )
        return results

    def _load_json_file(
        self,
        path: Path,
        *,
        fallback: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        if not path.exists():
            if fallback is not None:
                return fallback
            raise FileNotFoundError(f"file not found: {path}")

        with path.open("r", encoding="utf-8") as fh:
            loaded = json.load(fh)

        if not isinstance(loaded, dict):
            raise ValueError(f"json root must be object: {path}")
        return loaded

    def _write_json_file(self, path: Path, payload: dict[str, Any]) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        with path.open("w", encoding="utf-8") as fh:
            json.dump(payload, fh, ensure_ascii=False, indent=2)
            fh.write("\n")


def _utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()
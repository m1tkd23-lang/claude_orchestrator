# src\claude_orchestrator\application\usecases\save_requirements_usecase.py
from __future__ import annotations

from pathlib import Path
import json
from typing import Any

from jsonschema import Draft202012Validator

from claude_orchestrator.infrastructure.requirements_runtime import RequirementsRuntime


class SaveRequirementsUseCase:
    """requirements.json を schema 検証付きで保存する."""

    def execute(
        self,
        repo_path: str,
        requirements_json: dict[str, Any],
        *,
        changed_by: str = "system",
        change_summary: str | None = None,
        change_details: list[str] | None = None,
    ) -> dict[str, Any]:
        repo_root = Path(repo_path).resolve()
        runtime = RequirementsRuntime(repo_root)

        schema_path = runtime.paths.requirements_schema_json
        errors = self._validate_requirements_schema(
            schema_path=schema_path,
            requirements_json=requirements_json,
        )
        if errors:
            return {
                "ok": False,
                "repo_path": str(repo_root),
                "schema_path": str(schema_path),
                "requirements_path": str(runtime.paths.requirements_json),
                "errors": errors,
                "saved": False,
                "updated_at": None,
            }

        write_result = runtime.save_requirements_json(
            requirements_json=requirements_json,
            changed_by=changed_by,
            change_summary=change_summary,
            change_details=change_details,
        )

        return {
            "ok": True,
            "repo_path": str(repo_root),
            "schema_path": str(schema_path),
            "requirements_path": write_result.path,
            "errors": [],
            "saved": True,
            "updated_at": write_result.updated_at,
        }

    def _validate_requirements_schema(
        self,
        *,
        schema_path: Path,
        requirements_json: dict[str, Any],
    ) -> list[str]:
        if not schema_path.exists():
            return [f"Schema not found: {schema_path}"]

        with schema_path.open("r", encoding="utf-8") as fh:
            schema = json.load(fh)

        validator = Draft202012Validator(schema)
        raw_errors = sorted(
            validator.iter_errors(requirements_json),
            key=lambda err: list(err.path),
        )

        errors: list[str] = []
        for err in raw_errors:
            path_text = ".".join(str(part) for part in err.path) or "<root>"
            errors.append(f"{path_text}: {err.message}")

        return errors
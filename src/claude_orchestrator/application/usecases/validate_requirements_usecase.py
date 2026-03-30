# src\claude_orchestrator\application\usecases\validate_requirements_usecase.py
from __future__ import annotations

from pathlib import Path
import json
from typing import Any

from jsonschema import Draft202012Validator

from claude_orchestrator.infrastructure.requirements_runtime import RequirementsRuntime


class ValidateRequirementsUseCase:
    """requirements.json を schema 検証する."""

    def execute(
        self,
        repo_path: str,
        requirements_json: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        repo_root = Path(repo_path).resolve()
        runtime = RequirementsRuntime(repo_root)

        if requirements_json is None:
            try:
                requirements_json = runtime.load_requirements_json()
            except FileNotFoundError as exc:
                return {
                    "ok": False,
                    "valid": False,
                    "repo_path": str(repo_root),
                    "schema_path": str(runtime.paths.requirements_schema_json),
                    "requirements_path": str(runtime.paths.requirements_json),
                    "errors": [str(exc)],
                }

        schema_path = runtime.paths.requirements_schema_json
        errors = self._validate_requirements_schema(
            schema_path=schema_path,
            requirements_json=requirements_json,
        )

        return {
            "ok": not errors,
            "valid": not errors,
            "repo_path": str(repo_root),
            "schema_path": str(schema_path),
            "requirements_path": str(runtime.paths.requirements_json),
            "errors": errors,
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
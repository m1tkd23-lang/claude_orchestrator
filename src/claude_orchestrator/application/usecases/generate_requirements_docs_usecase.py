# src\claude_orchestrator\application\usecases\generate_requirements_docs_usecase.py
from __future__ import annotations

from pathlib import Path
from typing import Any
import json

from jsonschema import Draft202012Validator

from claude_orchestrator.infrastructure.requirements_runtime import RequirementsRuntime
from claude_orchestrator.services.requirements_doc_generator import (
    generate_requirements_docs,
)


class GenerateRequirementsDocsUseCase:
    """requirements.json から主要 docs を生成する."""

    def execute(self, repo_path: str) -> dict[str, Any]:
        repo_root = Path(repo_path).resolve()
        runtime = RequirementsRuntime(repo_root)
        requirements_json = runtime.load_requirements_json()

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
                "errors": errors,
                "written_files": [],
            }

        docs = generate_requirements_docs(requirements_json)
        written_files = runtime.write_generated_docs(docs)

        return {
            "ok": True,
            "repo_path": str(repo_root),
            "schema_path": str(schema_path),
            "errors": [],
            "written_files": [
                {
                    "path": item.path,
                    "updated_at": item.updated_at,
                }
                for item in written_files
            ],
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
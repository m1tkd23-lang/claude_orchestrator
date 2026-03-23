# src\claude_orchestrator\infrastructure\schema_validator.py
from __future__ import annotations

from pathlib import Path
import json

from jsonschema import Draft202012Validator


class SchemaValidator:
    def __init__(self, schemas_dir: Path) -> None:
        self.schemas_dir = schemas_dir.resolve()

    def validate_report(self, role: str, data: dict) -> None:
        schema_path = self._get_schema_path(role)
        if not schema_path.exists():
            raise FileNotFoundError(f"Schema not found: {schema_path}")

        with schema_path.open("r", encoding="utf-8") as f:
            schema = json.load(f)

        validator = Draft202012Validator(schema)
        errors = sorted(validator.iter_errors(data), key=lambda e: list(e.path))
        if errors:
            first = errors[0]
            path_text = ".".join(str(p) for p in first.path) or "<root>"
            raise ValueError(
                f"Schema validation failed for role={role} at {path_text}: {first.message}"
            )

    def _get_schema_path(self, role: str) -> Path:
        mapping = {
            "task_router": "task_router_report.schema.json",
            "implementer": "implementer_report.schema.json",
            "reviewer": "reviewer_report.schema.json",
            "director": "director_report.schema.json",
            "planner": "planner_report.schema.json",
            "planner_safe": "planner_report.schema.json",
            "planner_improvement": "planner_report.schema.json",
        }
        if role not in mapping:
            raise ValueError(f"Unsupported role: {role}")
        return self.schemas_dir / mapping[role]
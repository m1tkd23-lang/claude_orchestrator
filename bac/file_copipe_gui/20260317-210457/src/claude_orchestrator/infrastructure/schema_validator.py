# src\claude_orchestrator\infrastructure\schema_validator.py
from __future__ import annotations

from pathlib import Path
import json

from jsonschema import validate


class SchemaValidator:
    def __init__(self, schemas_dir: Path) -> None:
        self.schemas_dir = schemas_dir

    def validate_report(self, role: str, data: dict) -> None:
        schema = self._load_schema(role)
        validate(instance=data, schema=schema)

    def _load_schema(self, role: str) -> dict:
        if role == "implementer":
            path = self.schemas_dir / "implementer_report.schema.json"
        elif role == "reviewer":
            path = self.schemas_dir / "reviewer_report.schema.json"
        elif role == "director":
            path = self.schemas_dir / "director_report.schema.json"
        else:
            raise ValueError(f"Unsupported role: {role}")

        if not path.exists():
            raise FileNotFoundError(f"Schema not found: {path}")

        with path.open("r", encoding="utf-8") as f:
            return json.load(f)
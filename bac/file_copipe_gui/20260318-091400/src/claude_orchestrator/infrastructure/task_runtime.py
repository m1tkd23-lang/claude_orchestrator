# src\claude_orchestrator\infrastructure\task_runtime.py
from __future__ import annotations

from pathlib import Path
import json


class TaskRuntime:
    def __init__(self, target_repo: Path, task_id: str) -> None:
        self.target_repo = target_repo.resolve()
        self.root = self.target_repo / ".claude_orchestrator"
        self.task_dir = self.root / "tasks" / task_id
        self.task_json_path = self.task_dir / "task.json"
        self.state_json_path = self.task_dir / "state.json"
        self.inbox_dir = self.task_dir / "inbox"
        self.outbox_dir = self.task_dir / "outbox"
        self.logs_dir = self.task_dir / "logs"
        self.roles_dir = self.root / "roles"
        self.schemas_dir = self.root / "schemas"
        self.templates_dir = self.root / "templates"

    def ensure_exists(self) -> None:
        if not self.task_dir.exists():
            raise FileNotFoundError(f"Task directory not found: {self.task_dir}")

        if not self.task_json_path.exists():
            raise FileNotFoundError(f"task.json not found: {self.task_json_path}")

        if not self.state_json_path.exists():
            raise FileNotFoundError(f"state.json not found: {self.state_json_path}")

    def load_task_json(self) -> dict:
        self.ensure_exists()
        return self._load_json(self.task_json_path)

    def load_state_json(self) -> dict:
        self.ensure_exists()
        return self._load_json(self.state_json_path)

    def read_role_definition(self, role: str) -> str:
        path = self.roles_dir / f"{role}.md"
        if not path.exists():
            raise FileNotFoundError(f"Role definition not found: {path}")
        return path.read_text(encoding="utf-8")

    def read_template(self, role: str) -> str:
        path = self.templates_dir / f"{role}_prompt.txt"
        if not path.exists():
            raise FileNotFoundError(f"Prompt template not found: {path}")
        return path.read_text(encoding="utf-8")

    def read_schema_text(self, role: str) -> str:
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

        return path.read_text(encoding="utf-8")

    def get_output_json_path(self, role: str, cycle: int) -> Path:
        return self.inbox_dir / f"{role}_report_v{cycle}.json"

    def get_output_prompt_path(self, role: str, cycle: int) -> Path:
        return self.outbox_dir / f"{role}_prompt_v{cycle}.txt"

    def load_previous_director_report_text(self, cycle: int) -> str:
        if cycle <= 1:
            return "{}"

        path = self.inbox_dir / f"director_report_v{cycle - 1}.json"
        if not path.exists():
            return "{}"

        return path.read_text(encoding="utf-8")

    def load_required_report_text(self, role: str, cycle: int) -> str:
        if role == "reviewer":
            path = self.inbox_dir / f"implementer_report_v{cycle}.json"
        elif role == "director":
            path = self.inbox_dir / f"reviewer_report_v{cycle}.json"
        else:
            raise ValueError(f"Unsupported required report role: {role}")

        if not path.exists():
            raise FileNotFoundError(f"Required report not found: {path}")

        return path.read_text(encoding="utf-8")

    def load_implementer_report_text(self, cycle: int) -> str:
        path = self.inbox_dir / f"implementer_report_v{cycle}.json"
        if not path.exists():
            raise FileNotFoundError(f"Implementer report not found: {path}")
        return path.read_text(encoding="utf-8")

    def write_prompt(self, role: str, cycle: int, content: str) -> Path:
        path = self.get_output_prompt_path(role, cycle)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(content, encoding="utf-8")
        return path

    @staticmethod
    def _load_json(path: Path) -> dict:
        with path.open("r", encoding="utf-8") as f:
            return json.load(f)
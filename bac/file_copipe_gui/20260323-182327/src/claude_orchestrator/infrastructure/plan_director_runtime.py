# src\claude_orchestrator\infrastructure\plan_director_runtime.py
from __future__ import annotations

from pathlib import Path
import json

from claude_orchestrator.infrastructure.project_paths import ProjectPaths
from claude_orchestrator.infrastructure.task_runtime import TaskRuntime
from claude_orchestrator.infrastructure.task_index import TaskIndex


class PlanDirectorRuntime:
    _SUPPORTED_DEVELOPMENT_MODES = {
        "mainline",
        "maintenance",
    }
    _DEFAULT_DEVELOPMENT_MODE = "maintenance"

    def __init__(self, target_repo: Path, source_task_id: str) -> None:
        self.target_repo = target_repo.resolve()
        self.project_paths = ProjectPaths(target_repo=self.target_repo)
        self.project_paths.ensure_initialized()

        self.root = self.target_repo / ".claude_orchestrator"
        self.roles_dir = self.root / "roles"
        self.templates_dir = self.root / "templates"
        self.schemas_dir = self.root / "schemas"

        self.source_task_id = source_task_id
        self.source_runtime = TaskRuntime(
            target_repo=self.target_repo,
            task_id=source_task_id,
        )
        self.planner_dir = self.source_runtime.task_dir / "planner"

    def ensure_source_task_exists(self) -> None:
        self.source_runtime.ensure_exists()

    def ensure_completed_source_task(self) -> None:
        state_json = self.load_source_state_json()
        if str(state_json.get("status")) != "completed":
            raise ValueError(
                f"plan_director can run only for completed task. task_id={self.source_task_id}"
            )

    def load_source_task_json(self) -> dict:
        return self.source_runtime.load_task_json()

    def load_source_state_json(self) -> dict:
        return self.source_runtime.load_state_json()

    def load_project_config(self) -> dict:
        return self.project_paths.load_project_config()

    def get_development_mode(self) -> str:
        project_config = self.load_project_config()
        raw_value = str(
            project_config.get("development_mode", self._DEFAULT_DEVELOPMENT_MODE)
        ).strip()
        if raw_value in self._SUPPORTED_DEVELOPMENT_MODES:
            return raw_value
        return self._DEFAULT_DEVELOPMENT_MODE

    def read_role_definition(self) -> str:
        path = self.roles_dir / "plan_director.md"
        if not path.exists():
            raise FileNotFoundError(f"plan_director role definition not found: {path}")
        return path.read_text(encoding="utf-8")

    def read_template(self) -> str:
        path = self.templates_dir / "plan_director_prompt.txt"
        if not path.exists():
            raise FileNotFoundError(f"plan_director prompt template not found: {path}")
        return path.read_text(encoding="utf-8")

    def read_schema_text(self) -> str:
        path = self.schemas_dir / "plan_director_report.schema.json"
        if not path.exists():
            raise FileNotFoundError(f"plan_director schema not found: {path}")
        return path.read_text(encoding="utf-8")

    def get_report_path(self, cycle: int) -> Path:
        return self.planner_dir / f"plan_director_report_v{cycle}.json"

    def get_prompt_path(self, cycle: int) -> Path:
        return self.planner_dir / f"plan_director_prompt_v{cycle}.txt"

    def write_prompt(self, cycle: int, content: str) -> Path:
        path = self.get_prompt_path(cycle)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(content, encoding="utf-8")
        return path

    def load_source_reports_text(self, cycle: int) -> dict[str, str]:
        implementer_path = self.source_runtime.get_output_json_path("implementer", cycle)
        reviewer_path = self.source_runtime.get_output_json_path("reviewer", cycle)
        director_path = self.source_runtime.get_output_json_path("director", cycle)

        missing_paths = [
            str(path)
            for path in [implementer_path, reviewer_path, director_path]
            if not path.exists()
        ]
        if missing_paths:
            raise FileNotFoundError(
                "Required source reports not found: " + ", ".join(missing_paths)
            )

        return {
            "implementer_report_json": implementer_path.read_text(encoding="utf-8"),
            "reviewer_report_json": reviewer_path.read_text(encoding="utf-8"),
            "director_report_json": director_path.read_text(encoding="utf-8"),
        }

    def load_planner_report_text(self, planner_role: str, cycle: int) -> str:
        if planner_role not in {"planner_safe", "planner_improvement"}:
            raise ValueError(f"Unsupported planner role: {planner_role}")

        path = self.planner_dir / f"{planner_role}_report_v{cycle}.json"
        if not path.exists():
            return "null"
        return path.read_text(encoding="utf-8")

    def load_planner_state_text(self, planner_role: str, cycle: int) -> str:
        if planner_role not in {"planner_safe", "planner_improvement"}:
            raise ValueError(f"Unsupported planner role: {planner_role}")

        path = self.planner_dir / f"{planner_role}_proposal_states_v{cycle}.json"
        if not path.exists():
            return "null"
        return path.read_text(encoding="utf-8")

    def build_task_list_summary(self) -> str:
        index = TaskIndex(tasks_root=self.project_paths.tasks_dir)
        tasks = index.list_task_statuses()
        if not tasks:
            return "[]"
        return json.dumps(tasks, indent=2, ensure_ascii=False)
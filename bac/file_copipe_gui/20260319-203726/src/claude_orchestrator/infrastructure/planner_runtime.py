# src\claude_orchestrator\infrastructure\planner_runtime.py
from __future__ import annotations

from pathlib import Path
import json

from claude_orchestrator.infrastructure.project_paths import ProjectPaths
from claude_orchestrator.infrastructure.task_runtime import TaskRuntime
from claude_orchestrator.infrastructure.task_index import TaskIndex


class PlannerRuntime:
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

    def load_source_task_json(self) -> dict:
        return self.source_runtime.load_task_json()

    def load_source_state_json(self) -> dict:
        return self.source_runtime.load_state_json()

    def ensure_completed_source_task(self) -> None:
        state_json = self.load_source_state_json()
        if str(state_json.get("status")) != "completed":
            raise ValueError(
                f"Planner can run only for completed task. task_id={self.source_task_id}"
            )

    def read_role_definition(self) -> str:
        path = self.roles_dir / "planner.md"
        if not path.exists():
            raise FileNotFoundError(f"Planner role definition not found: {path}")
        return path.read_text(encoding="utf-8")

    def read_template(self) -> str:
        path = self.templates_dir / "planner_prompt.txt"
        if not path.exists():
            raise FileNotFoundError(f"Planner prompt template not found: {path}")
        return path.read_text(encoding="utf-8")

    def read_schema_text(self) -> str:
        path = self.schemas_dir / "planner_report.schema.json"
        if not path.exists():
            raise FileNotFoundError(f"Planner schema not found: {path}")
        return path.read_text(encoding="utf-8")

    def get_report_path(self, cycle: int) -> Path:
        return self.planner_dir / f"planner_report_v{cycle}.json"

    def get_prompt_path(self, cycle: int) -> Path:
        return self.planner_dir / f"planner_prompt_v{cycle}.txt"

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

    def build_task_list_summary(self) -> str:
        index = TaskIndex(tasks_root=self.project_paths.tasks_dir)
        tasks = index.list_task_statuses()
        if not tasks:
            return "[]"
        return json.dumps(tasks, indent=2, ensure_ascii=False)

    def build_reference_docs_text(self, reference_doc_paths: list[str] | None) -> str:
        if not reference_doc_paths:
            return "[]"

        docs_payload: list[dict[str, str]] = []
        for relative_path in reference_doc_paths:
            doc_path = self.target_repo / relative_path
            if not doc_path.exists():
                docs_payload.append(
                    {
                        "path": relative_path,
                        "status": "missing",
                        "content": "",
                    }
                )
                continue

            docs_payload.append(
                {
                    "path": relative_path,
                    "status": "ok",
                    "content": doc_path.read_text(encoding="utf-8"),
                }
            )

        return json.dumps(docs_payload, indent=2, ensure_ascii=False)

    def build_core_docs_text(self, relative_paths: list[str]) -> str:
        return self.source_runtime.build_core_docs_text(relative_paths)
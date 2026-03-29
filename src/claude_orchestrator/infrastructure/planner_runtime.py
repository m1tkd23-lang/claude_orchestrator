# src/claude_orchestrator/infrastructure/planner_runtime.py
from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path
import json

from claude_orchestrator.infrastructure.project_paths import ProjectPaths
from claude_orchestrator.infrastructure.task_runtime import TaskRuntime
from claude_orchestrator.infrastructure.task_index import TaskIndex
from claude_orchestrator.services.context_compactor import (
    build_director_context_for_next_role,
    build_implementer_context_for_reviewer,
    build_reviewer_context_for_director,
)
from claude_orchestrator.services.docs_context_compactor import compact_core_doc_text


class PlannerRuntime:
    _ROLE_TO_TEMPLATE = {
        "planner_safe": "planner_safe_prompt.txt",
        "planner_improvement": "planner_improvement_prompt.txt",
    }

    _ROLE_TO_DEFINITION = {
        "planner_safe": "planner_safe.md",
        "planner_improvement": "planner_improvement.md",
    }

    _ROLE_TO_REPORT_FILENAME = {
        "planner_safe": "planner_safe_report_v{cycle}.json",
        "planner_improvement": "planner_improvement_report_v{cycle}.json",
    }

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

    def read_role_definition(self, planner_role: str) -> str:
        path = self.roles_dir / self._get_role_definition_name(planner_role)
        if not path.exists():
            raise FileNotFoundError(f"Planner role definition not found: {path}")
        return path.read_text(encoding="utf-8")

    def read_template(self, planner_role: str) -> str:
        path = self.templates_dir / self._get_template_name(planner_role)
        if not path.exists():
            raise FileNotFoundError(f"Planner prompt template not found: {path}")
        return path.read_text(encoding="utf-8")

    def read_schema_text(self) -> str:
        path = self.schemas_dir / "planner_report.schema.json"
        if not path.exists():
            raise FileNotFoundError(f"Planner schema not found: {path}")
        return path.read_text(encoding="utf-8")

    def get_report_path(self, cycle: int, planner_role: str) -> Path:
        filename = self._get_report_filename(planner_role).format(cycle=cycle)
        return self.planner_dir / filename

    def get_prompt_path(self, cycle: int, planner_role: str) -> Path:
        return self.planner_dir / f"{planner_role}_prompt_v{cycle}.txt"

    def get_proposals_dir(self, cycle: int, planner_role: str) -> Path:
        normalized = self.validate_planner_role(planner_role)
        return self.planner_dir / "proposals" / normalized / f"cycle_{cycle}"

    def get_proposal_path(
        self,
        *,
        cycle: int,
        planner_role: str,
        proposal_id: str,
    ) -> Path:
        normalized_role = self.validate_planner_role(planner_role)
        normalized_proposal_id = str(proposal_id).strip()
        if not normalized_proposal_id:
            raise ValueError("proposal_id must not be empty")
        return (
            self.get_proposals_dir(cycle=cycle, planner_role=normalized_role)
            / f"{normalized_proposal_id}.json"
        )

    def write_prompt(self, cycle: int, planner_role: str, content: str) -> Path:
        path = self.get_prompt_path(cycle=cycle, planner_role=planner_role)
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

        implementer_json = self._load_json(implementer_path)
        reviewer_json = self._load_json(reviewer_path)
        director_json = self._load_json(director_path)

        return {
            "implementer_report_json": json.dumps(
                build_implementer_context_for_reviewer(implementer_json),
                indent=2,
                ensure_ascii=False,
            ),
            "reviewer_report_json": json.dumps(
                build_reviewer_context_for_director(reviewer_json),
                indent=2,
                ensure_ascii=False,
            ),
            "director_report_json": json.dumps(
                build_director_context_for_next_role(director_json),
                indent=2,
                ensure_ascii=False,
            ),
        }

    def build_task_list_summary(self) -> str:
        index = TaskIndex(tasks_root=self.project_paths.tasks_dir)
        tasks = index.list_task_summaries_for_planner()
        if not tasks:
            return "[]"
        return json.dumps(tasks, indent=2, ensure_ascii=False)

    def build_reference_docs_text(self, reference_doc_paths: list[str] | None) -> str:
        if not reference_doc_paths:
            return "[]"

        docs_payload: list[dict[str, str]] = []
        for relative_path in reference_doc_paths:
            normalized = str(relative_path).strip()
            if not normalized:
                continue

            doc_path = self.target_repo / normalized
            if not doc_path.exists():
                continue

            docs_payload.append(
                {
                    "path": normalized,
                    "status": "ok",
                    "content": doc_path.read_text(encoding="utf-8"),
                }
            )

        if not docs_payload:
            return "[]"

        return json.dumps(docs_payload, indent=2, ensure_ascii=False)

    def build_core_docs_text(self, relative_paths: list[str]) -> str:
        sections: list[str] = []

        for relative_path in relative_paths:
            normalized = self.source_runtime._normalize_doc_display_path(relative_path)
            content = self.source_runtime.read_doc_text(relative_path)
            compact_content = compact_core_doc_text(relative_path, content)
            sections.append(f"## doc: {normalized}\n{compact_content}")

        return "\n\n".join(sections)

    def write_proposal_files(
        self,
        *,
        cycle: int,
        planner_role: str,
        planner_report: dict,
    ) -> list[Path]:
        normalized_role = self.validate_planner_role(planner_role)
        proposals = planner_report.get("proposals", []) or []
        if not isinstance(proposals, list):
            raise ValueError("planner_report.proposals must be an array")

        now_text = self._current_timestamp_text()
        written_paths: list[Path] = []

        for proposal in proposals:
            if not isinstance(proposal, dict):
                raise ValueError("Each planner proposal must be an object")

            proposal_id = str(proposal.get("proposal_id", "")).strip()
            if not proposal_id:
                raise ValueError("planner proposal_id must not be empty")

            proposal_path = self.get_proposal_path(
                cycle=cycle,
                planner_role=normalized_role,
                proposal_id=proposal_id,
            )
            proposal_path.parent.mkdir(parents=True, exist_ok=True)

            enriched = self._build_proposal_document(
                proposal=proposal,
                proposal_path=proposal_path,
                now_text=now_text,
            )

            with proposal_path.open("w", encoding="utf-8") as f:
                json.dump(enriched, f, ensure_ascii=False, indent=2)
                f.write("\n")

            written_paths.append(proposal_path)

        return written_paths

    def _build_proposal_document(
        self,
        *,
        proposal: dict,
        proposal_path: Path,
        now_text: str,
    ) -> dict:
        document = json.loads(json.dumps(proposal, ensure_ascii=False))

        relative_path = proposal_path.relative_to(self.target_repo).as_posix()
        existing_meta = document.get("_meta")
        meta = existing_meta if isinstance(existing_meta, dict) else {}
        meta["relative_path"] = relative_path
        document["_meta"] = meta

        if "state" not in document:
            document["state"] = "proposed"
        if "created_task_id" not in document:
            document["created_task_id"] = None
        if not str(document.get("created_at", "")).strip():
            document["created_at"] = now_text
        if not str(document.get("updated_at", "")).strip():
            document["updated_at"] = now_text

        return document

    @staticmethod
    def _current_timestamp_text() -> str:
        return (
            datetime.now(timezone.utc)
            .replace(microsecond=0)
            .isoformat()
            .replace("+00:00", "Z")
        )

    @classmethod
    def validate_planner_role(cls, planner_role: str) -> str:
        normalized = str(planner_role).strip()
        if normalized not in cls._ROLE_TO_TEMPLATE:
            raise ValueError(f"Unsupported planner role: {planner_role}")
        return normalized

    @classmethod
    def _get_template_name(cls, planner_role: str) -> str:
        normalized = cls.validate_planner_role(planner_role)
        return cls._ROLE_TO_TEMPLATE[normalized]

    @classmethod
    def _get_role_definition_name(cls, planner_role: str) -> str:
        normalized = cls.validate_planner_role(planner_role)
        return cls._ROLE_TO_DEFINITION[normalized]

    @classmethod
    def _get_report_filename(cls, planner_role: str) -> str:
        normalized = cls.validate_planner_role(planner_role)
        return cls._ROLE_TO_REPORT_FILENAME[normalized]

    @staticmethod
    def _load_json(path: Path) -> dict:
        with path.open("r", encoding="utf-8") as f:
            return json.load(f)
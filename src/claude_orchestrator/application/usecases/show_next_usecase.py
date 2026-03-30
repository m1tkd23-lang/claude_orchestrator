# src\claude_orchestrator\application\usecases\show_next_usecase.py
from __future__ import annotations

from pathlib import Path
import json

from claude_orchestrator.application.usecases.retrieve_memory_for_prompt_usecase import (
    RetrieveMemoryForPromptUseCase,
)
from claude_orchestrator.core.prompt_renderer import render_prompt
from claude_orchestrator.infrastructure.project_paths import ProjectPaths
from claude_orchestrator.infrastructure.task_runtime import TaskRuntime
from claude_orchestrator.services.context_compactor import (
    compact_task_json_for_execution_role,
)


class ShowNextUseCase:
    CORE_DOC_PATHS_FOR_TASK_ROUTER = [
        ".claude_orchestrator/docs/project_core/開発の目的本筋.md",
        ".claude_orchestrator/docs/task_maps/planner_task_router判断材料マップ.md",
        ".claude_orchestrator/docs/completion_definition.md",
        ".claude_orchestrator/docs/task_splitting_rules.md",
    ]

    def execute(self, repo_path: str, task_id: str) -> dict:
        target_repo = Path(repo_path).resolve()
        project_paths = ProjectPaths(target_repo=target_repo)
        project_paths.ensure_initialized()

        runtime = TaskRuntime(target_repo=target_repo, task_id=task_id)
        task_json = runtime.load_task_json()
        state_json = runtime.load_state_json()

        role = str(state_json["next_role"])
        cycle = int(state_json["cycle"])
        revision = int(state_json.get("revision", 1))

        if role == "none":
            raise ValueError(f"Task already finished or no next role: {task_id}")

        role_definition = runtime.read_role_definition(role)
        template = runtime.read_template(role)
        output_schema = runtime.read_schema_text(role)
        output_json_path = runtime.get_output_json_path(role, cycle)

        prompt_text = self._build_prompt(
            role=role,
            task_id=task_id,
            cycle=cycle,
            repo_path=str(target_repo),
            runtime=runtime,
            template=template,
            role_definition=role_definition,
            task_json=task_json,
            state_json=state_json,
            output_schema=output_schema,
            output_json_path=output_json_path,
        )

        prompt_path = runtime.write_prompt(role=role, cycle=cycle, content=prompt_text)

        return {
            "task_id": task_id,
            "role": role,
            "cycle": cycle,
            "revision": revision,
            "prompt_path": str(prompt_path),
            "output_json_path": str(output_json_path),
            "state_snapshot": {
                "current_stage": str(state_json.get("current_stage", "")),
                "next_role": role,
                "cycle": cycle,
                "revision": revision,
                "status": str(state_json.get("status", "")),
                "last_completed_role": str(state_json.get("last_completed_role", "")),
            },
        }

    def _build_prompt(
        self,
        role: str,
        task_id: str,
        cycle: int,
        repo_path: str,
        runtime: TaskRuntime,
        template: str,
        role_definition: str,
        task_json: dict,
        state_json: dict,
        output_schema: str,
        output_json_path: Path,
    ) -> str:
        prompt_task_json = (
            compact_task_json_for_execution_role(role, task_json)
            if role in {"implementer", "reviewer", "director"}
            else task_json
        )
        task_json_text = json.dumps(prompt_task_json, indent=2, ensure_ascii=False)
        state_json_text = json.dumps(state_json, indent=2, ensure_ascii=False)

        common_kwargs = {
            "role_definition": role_definition,
            "task_json": task_json_text,
            "state_json": state_json_text,
            "output_schema": output_schema,
            "output_json_path": str(output_json_path),
            "target_repo": repo_path,
            "task_id": task_id,
            "cycle": str(cycle),
        }

        if role == "task_router":
            recalled_notes = RetrieveMemoryForPromptUseCase().execute(
                repo_path=repo_path,
                role=role,
                task_json=task_json,
                state_json=state_json,
                development_mode=self._load_development_mode(
                    target_repo=Path(repo_path).resolve()
                ),
            )
            task_router_skill = runtime.read_skill_text("task_router", "route-task")
            core_docs_text = runtime.build_core_docs_text(
                self.CORE_DOC_PATHS_FOR_TASK_ROUTER
            )
            return render_prompt(
                template,
                task_router_skill=task_router_skill,
                core_docs_text=core_docs_text,
                recalled_notes_text=recalled_notes["recalled_notes_text"],
                **common_kwargs,
            )

        if role == "implementer":
            recalled_notes = RetrieveMemoryForPromptUseCase().execute(
                repo_path=repo_path,
                role=role,
                task_json=task_json,
                state_json=state_json,
                development_mode=self._load_development_mode(
                    target_repo=Path(repo_path).resolve()
                ),
            )
            previous_director_report_json = runtime.load_previous_director_context_text(
                cycle
            )
            assigned_skills_text = runtime.read_role_skills_text("implementer", task_json)
            return render_prompt(
                template,
                previous_director_report_json=previous_director_report_json,
                assigned_skills_text=assigned_skills_text,
                recalled_notes_text=recalled_notes["recalled_notes_text"],
                **common_kwargs,
            )

        if role == "reviewer":
            implementer_report_json = (
                runtime.load_implementer_context_for_reviewer_text(cycle)
            )
            assigned_skills_text = runtime.read_role_skills_text("reviewer", task_json)
            return render_prompt(
                template,
                implementer_report_json=implementer_report_json,
                assigned_skills_text=assigned_skills_text,
                **common_kwargs,
            )

        if role == "director":
            implementer_report_json = (
                runtime.load_implementer_context_for_reviewer_text(cycle)
            )
            reviewer_report_json = runtime.load_reviewer_context_for_director_text(cycle)
            assigned_skills_text = runtime.read_role_skills_text("director", task_json)
            return render_prompt(
                template,
                implementer_report_json=implementer_report_json,
                reviewer_report_json=reviewer_report_json,
                assigned_skills_text=assigned_skills_text,
                **common_kwargs,
            )

        raise ValueError(f"Unsupported role: {role}")

    @staticmethod
    def _load_development_mode(*, target_repo: Path) -> str:
        project_paths = ProjectPaths(target_repo=target_repo)
        project_config = project_paths.load_project_config()
        value = str(project_config.get("development_mode", "")).strip()
        return value or "maintenance"
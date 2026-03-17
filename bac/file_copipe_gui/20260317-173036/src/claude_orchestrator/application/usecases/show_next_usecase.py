# src\claude_orchestrator\application\usecases\show_next_usecase.py
from __future__ import annotations

from pathlib import Path
import json

from claude_orchestrator.core.prompt_renderer import render_prompt
from claude_orchestrator.infrastructure.project_paths import ProjectPaths
from claude_orchestrator.infrastructure.task_runtime import TaskRuntime


class ShowNextUseCase:
    def execute(self, repo_path: str, task_id: str) -> dict:
        target_repo = Path(repo_path).resolve()
        project_paths = ProjectPaths(target_repo=target_repo)
        project_paths.ensure_initialized()

        runtime = TaskRuntime(target_repo=target_repo, task_id=task_id)
        task_json = runtime.load_task_json()
        state_json = runtime.load_state_json()

        role = str(state_json["next_role"])
        cycle = int(state_json["cycle"])

        if role == "none":
            raise ValueError(f"Task already finished or no next role: {task_id}")

        role_definition = runtime.read_role_definition(role)
        template = runtime.read_template(role)
        output_schema = runtime.read_schema_text(role)
        output_json_path = runtime.get_output_json_path(role, cycle)

        prompt_text = self._build_prompt(
            role=role,
            cycle=cycle,
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
            "prompt_path": str(prompt_path),
            "output_json_path": str(output_json_path),
        }

    def _build_prompt(
        self,
        role: str,
        cycle: int,
        runtime: TaskRuntime,
        template: str,
        role_definition: str,
        task_json: dict,
        state_json: dict,
        output_schema: str,
        output_json_path: Path,
    ) -> str:
        task_json_text = json.dumps(task_json, indent=2, ensure_ascii=False)
        state_json_text = json.dumps(state_json, indent=2, ensure_ascii=False)

        if role == "implementer":
            previous_director_report_json = runtime.load_previous_director_report_text(cycle)
            return render_prompt(
                template,
                role_definition=role_definition,
                task_json=task_json_text,
                state_json=state_json_text,
                previous_director_report_json=previous_director_report_json,
                output_schema=output_schema,
                output_json_path=str(output_json_path),
            )

        if role == "reviewer":
            implementer_report_json = runtime.load_required_report_text("reviewer", cycle)
            return render_prompt(
                template,
                role_definition=role_definition,
                task_json=task_json_text,
                state_json=state_json_text,
                implementer_report_json=implementer_report_json,
                output_schema=output_schema,
                output_json_path=str(output_json_path),
            )

        if role == "director":
            implementer_report_json = runtime.load_implementer_report_text(cycle)
            reviewer_report_json = runtime.load_required_report_text("director", cycle)
            return render_prompt(
                template,
                role_definition=role_definition,
                task_json=task_json_text,
                state_json=state_json_text,
                implementer_report_json=implementer_report_json,
                reviewer_report_json=reviewer_report_json,
                output_schema=output_schema,
                output_json_path=str(output_json_path),
            )

        raise ValueError(f"Unsupported role: {role}")
# src\claude_orchestrator\application\usecases\run_plan_director_usecase.py
from __future__ import annotations

from pathlib import Path
import json

from claude_orchestrator.core.prompt_renderer import render_prompt
from claude_orchestrator.gui.claude_runner import run_claude_print_mode
from claude_orchestrator.infrastructure.plan_director_runtime import PlanDirectorRuntime
from claude_orchestrator.infrastructure.schema_validator import SchemaValidator
from claude_orchestrator.services.planning_context_compactor import (
    compact_project_config_for_plan_director,
    compact_state_json_for_planning,
    compact_task_json_for_plan_director,
)


class RunPlanDirectorUseCase:
    CORE_DOC_PATHS_FOR_PLAN_DIRECTOR = [
        ".claude_orchestrator/docs/completion_definition.md",
        ".claude_orchestrator/docs/feature_inventory.md",
    ]

    def execute(
        self,
        *,
        repo_path: str,
        source_task_id: str,
    ) -> dict:
        target_repo = Path(repo_path).resolve()
        runtime = PlanDirectorRuntime(
            target_repo=target_repo,
            source_task_id=source_task_id,
        )

        runtime.ensure_source_task_exists()
        runtime.ensure_completed_source_task()

        task_json = runtime.load_source_task_json()
        state_json = runtime.load_source_state_json()
        project_config = runtime.load_project_config()
        development_mode = runtime.get_development_mode()
        cycle = int(state_json["cycle"])

        role_definition = runtime.read_role_definition()
        template = runtime.read_template()
        output_schema = runtime.read_schema_text()
        output_json_path = runtime.get_report_path(cycle)

        reports_text = runtime.load_source_reports_text(cycle)
        planner_safe_report_json = runtime.load_planner_report_text("planner_safe", cycle)
        planner_improvement_report_json = runtime.load_planner_report_text(
            "planner_improvement",
            cycle,
        )
        planner_safe_state_json = runtime.load_planner_state_text("planner_safe", cycle)
        planner_improvement_state_json = runtime.load_planner_state_text(
            "planner_improvement",
            cycle,
        )
        task_list_summary = runtime.build_task_list_summary()
        core_docs_text = runtime.build_core_docs_text(
            self.CORE_DOC_PATHS_FOR_PLAN_DIRECTOR
        )

        prompt_text = self._build_prompt(
            source_task_id=source_task_id,
            cycle=cycle,
            repo_path=str(target_repo),
            development_mode=development_mode,
            project_config=project_config,
            role_definition=role_definition,
            template=template,
            task_json=task_json,
            state_json=state_json,
            implementer_report_json=reports_text["implementer_report_json"],
            reviewer_report_json=reports_text["reviewer_report_json"],
            director_report_json=reports_text["director_report_json"],
            planner_safe_report_json=planner_safe_report_json,
            planner_improvement_report_json=planner_improvement_report_json,
            planner_safe_state_json=planner_safe_state_json,
            planner_improvement_state_json=planner_improvement_state_json,
            task_list_summary=task_list_summary,
            core_docs_text=core_docs_text,
            output_schema=output_schema,
            output_json_path=output_json_path,
        )

        prompt_path = runtime.write_prompt(cycle=cycle, content=prompt_text)

        claude_result = run_claude_print_mode(
            repo_path=repo_path,
            prompt_text=prompt_text,
            output_json_path=str(output_json_path),
        )

        if not output_json_path.exists():
            raise RuntimeError(
                "claude command failed while running plan_director and no report was generated. "
                f"returncode={claude_result.returncode}, stderr={claude_result.stderr.strip()}"
            )

        with output_json_path.open("r", encoding="utf-8") as f:
            report = json.load(f)

        SchemaValidator(runtime.schemas_dir).validate_report(
            role="plan_director",
            data=report,
        )
        self._check_identity(
            expected_source_task_id=source_task_id,
            expected_cycle=cycle,
            report=report,
        )

        return {
            "source_task_id": source_task_id,
            "development_mode": development_mode,
            "cycle": cycle,
            "prompt_path": str(prompt_path),
            "output_json_path": str(output_json_path),
            "plan_director_report": report,
            "stdout": claude_result.stdout,
            "stderr": claude_result.stderr,
            "returncode": claude_result.returncode,
        }

    def _build_prompt(
        self,
        *,
        source_task_id: str,
        cycle: int,
        repo_path: str,
        development_mode: str,
        project_config: dict,
        role_definition: str,
        template: str,
        task_json: dict,
        state_json: dict,
        implementer_report_json: str,
        reviewer_report_json: str,
        director_report_json: str,
        planner_safe_report_json: str,
        planner_improvement_report_json: str,
        planner_safe_state_json: str,
        planner_improvement_state_json: str,
        task_list_summary: str,
        core_docs_text: str,
        output_schema: str,
        output_json_path: Path,
    ) -> str:
        task_json_text = json.dumps(
            compact_task_json_for_plan_director(task_json),
            indent=2,
            ensure_ascii=False,
        )
        state_json_text = json.dumps(
            compact_state_json_for_planning(state_json),
            indent=2,
            ensure_ascii=False,
        )
        project_config_json_text = json.dumps(
            compact_project_config_for_plan_director(project_config),
            indent=2,
            ensure_ascii=False,
        )

        return render_prompt(
            template,
            role_definition=role_definition,
            task_json=task_json_text,
            state_json=state_json_text,
            project_config_json=project_config_json_text,
            development_mode=development_mode,
            core_docs_text=core_docs_text,
            implementer_report_json=implementer_report_json,
            reviewer_report_json=reviewer_report_json,
            director_report_json=director_report_json,
            planner_safe_report_json=planner_safe_report_json,
            planner_improvement_report_json=planner_improvement_report_json,
            planner_safe_state_json=planner_safe_state_json,
            planner_improvement_state_json=planner_improvement_state_json,
            task_list_summary=task_list_summary,
            output_schema=output_schema,
            output_json_path=str(output_json_path),
            target_repo=repo_path,
            task_id=source_task_id,
            cycle=str(cycle),
        )

    @staticmethod
    def _check_identity(
        *,
        expected_source_task_id: str,
        expected_cycle: int,
        report: dict,
    ) -> None:
        if str(report.get("source_task_id")) != str(expected_source_task_id):
            raise ValueError(
                "source_task_id mismatch: "
                f"expected={expected_source_task_id}, actual={report.get('source_task_id')}"
            )

        if str(report.get("role")) != "plan_director":
            raise ValueError(
                f"role mismatch: expected=plan_director, actual={report.get('role')}"
            )

        if int(report.get("cycle")) != int(expected_cycle):
            raise ValueError(
                f"cycle mismatch: expected={expected_cycle}, actual={report.get('cycle')}"
            )
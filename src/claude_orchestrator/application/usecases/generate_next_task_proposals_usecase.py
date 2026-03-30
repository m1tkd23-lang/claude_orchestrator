# src\claude_orchestrator\application\usecases\generate_next_task_proposals_usecase.py
from __future__ import annotations

from pathlib import Path
import json

from claude_orchestrator.core.prompt_renderer import render_prompt
from claude_orchestrator.gui.claude_runner import run_claude_print_mode
from claude_orchestrator.infrastructure.planner_runtime import PlannerRuntime
from claude_orchestrator.infrastructure.schema_validator import SchemaValidator
from claude_orchestrator.services.planning_context_compactor import (
    compact_project_config_for_planner,
    compact_state_json_for_planning,
    compact_task_json_for_planner,
)


class GenerateNextTaskProposalsUseCase:
    CORE_DOC_PATHS_FOR_PLANNER = [
        ".claude_orchestrator/docs/project_core/開発の目的本筋.md",
        ".claude_orchestrator/docs/task_maps/planner_task_router判断材料マップ.md",
        ".claude_orchestrator/docs/task_maps/role別最小参照マップ.md",
        ".claude_orchestrator/docs/task_maps/TASKフロー全体図.md",
        ".claude_orchestrator/docs/task_history/過去TASK作業記録.md",
        ".claude_orchestrator/docs/completion_definition.md",
        ".claude_orchestrator/docs/feature_inventory.md",
    ]

    def execute(
        self,
        repo_path: str,
        source_task_id: str,
        reference_doc_paths: list[str] | None = None,
        planner_role: str = "planner_safe",
    ) -> dict:
        target_repo = Path(repo_path).resolve()
        runtime = PlannerRuntime(
            target_repo=target_repo,
            source_task_id=source_task_id,
        )
        planner_role = runtime.validate_planner_role(planner_role)

        runtime.ensure_source_task_exists()
        runtime.ensure_completed_source_task()

        task_json = runtime.load_source_task_json()
        state_json = runtime.load_source_state_json()
        project_config = runtime.load_project_config()
        development_mode = runtime.get_development_mode()
        cycle = int(state_json["cycle"])

        role_definition = runtime.read_role_definition(planner_role)
        template = runtime.read_template(planner_role)
        output_schema = runtime.read_schema_text()
        output_json_path = runtime.get_report_path(cycle=cycle, planner_role=planner_role)

        reports_text = runtime.load_source_reports_text(cycle)
        task_list_summary = runtime.build_task_list_summary()
        reference_docs = runtime.build_reference_docs_text(reference_doc_paths)
        core_docs_text = runtime.build_core_docs_text(self.CORE_DOC_PATHS_FOR_PLANNER)

        prompt_text = self._build_prompt(
            source_task_id=source_task_id,
            cycle=cycle,
            repo_path=str(target_repo),
            planner_role=planner_role,
            development_mode=development_mode,
            project_config=project_config,
            role_definition=role_definition,
            template=template,
            task_json=task_json,
            state_json=state_json,
            implementer_report_json=reports_text["implementer_report_json"],
            reviewer_report_json=reports_text["reviewer_report_json"],
            director_report_json=reports_text["director_report_json"],
            task_list_summary=task_list_summary,
            reference_docs=reference_docs,
            core_docs_text=core_docs_text,
            output_schema=output_schema,
            output_json_path=output_json_path,
        )

        prompt_path = runtime.write_prompt(
            cycle=cycle,
            planner_role=planner_role,
            content=prompt_text,
        )

        claude_result = run_claude_print_mode(
            repo_path=repo_path,
            prompt_text=prompt_text,
            output_json_path=str(output_json_path),
        )

        if not output_json_path.exists():
            raise RuntimeError(
                "claude command failed while generating planner proposals and no report was generated. "
                f"returncode={claude_result.returncode}, stderr={claude_result.stderr.strip()}"
            )

        with output_json_path.open("r", encoding="utf-8") as f:
            planner_report = json.load(f)

        validator = SchemaValidator(runtime.schemas_dir)
        validator.validate_report(
            role=planner_role,
            data=planner_report,
        )
        self._check_identity(
            expected_source_task_id=source_task_id,
            expected_cycle=cycle,
            expected_role=planner_role,
            report=planner_report,
        )

        proposal_paths = runtime.write_proposal_files(
            cycle=cycle,
            planner_role=planner_role,
            planner_report=planner_report,
        )
        for proposal_path in proposal_paths:
            with proposal_path.open("r", encoding="utf-8") as f:
                proposal_data = json.load(f)
            validator.validate_proposal(data=proposal_data)

        return {
            "source_task_id": source_task_id,
            "planner_role": planner_role,
            "development_mode": development_mode,
            "cycle": cycle,
            "prompt_path": str(prompt_path),
            "output_json_path": str(output_json_path),
            "proposal_paths": [str(path) for path in proposal_paths],
            "planner_report": planner_report,
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
        planner_role: str,
        development_mode: str,
        project_config: dict,
        role_definition: str,
        template: str,
        task_json: dict,
        state_json: dict,
        implementer_report_json: str,
        reviewer_report_json: str,
        director_report_json: str,
        task_list_summary: str,
        reference_docs: str,
        core_docs_text: str,
        output_schema: str,
        output_json_path: Path,
    ) -> str:
        task_json_text = json.dumps(
            compact_task_json_for_planner(task_json),
            indent=2,
            ensure_ascii=False,
        )
        state_json_text = json.dumps(
            compact_state_json_for_planning(state_json),
            indent=2,
            ensure_ascii=False,
        )
        project_config_json_text = json.dumps(
            compact_project_config_for_planner(project_config),
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
            implementer_report_json=implementer_report_json,
            reviewer_report_json=reviewer_report_json,
            director_report_json=director_report_json,
            task_list_summary=task_list_summary,
            reference_docs=reference_docs,
            core_docs_text=core_docs_text,
            output_schema=output_schema,
            output_json_path=str(output_json_path),
            target_repo=repo_path,
            task_id=source_task_id,
            cycle=str(cycle),
            planner_role=planner_role,
        )

    @staticmethod
    def _check_identity(
        *,
        expected_source_task_id: str,
        expected_cycle: int,
        expected_role: str,
        report: dict,
    ) -> None:
        if str(report.get("source_task_id")) != str(expected_source_task_id):
            raise ValueError(
                "source_task_id mismatch: "
                f"expected={expected_source_task_id}, actual={report.get('source_task_id')}"
            )

        if str(report.get("role")) != expected_role:
            raise ValueError(
                f"role mismatch: expected={expected_role}, actual={report.get('role')}"
            )

        if int(report.get("cycle")) != int(expected_cycle):
            raise ValueError(
                f"cycle mismatch: expected={expected_cycle}, actual={report.get('cycle')}"
            )
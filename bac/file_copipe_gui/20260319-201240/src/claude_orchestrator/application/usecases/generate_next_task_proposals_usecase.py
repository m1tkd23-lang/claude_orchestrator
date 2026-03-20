# src\claude_orchestrator\application\usecases\generate_next_task_proposals_usecase.py
from __future__ import annotations

from pathlib import Path
import json

from claude_orchestrator.core.prompt_renderer import render_prompt
from claude_orchestrator.gui.claude_runner import run_claude_print_mode
from claude_orchestrator.infrastructure.planner_runtime import PlannerRuntime
from claude_orchestrator.infrastructure.schema_validator import SchemaValidator


class GenerateNextTaskProposalsUseCase:
    def execute(
        self,
        repo_path: str,
        source_task_id: str,
        reference_doc_paths: list[str] | None = None,
    ) -> dict:
        target_repo = Path(repo_path).resolve()
        runtime = PlannerRuntime(
            target_repo=target_repo,
            source_task_id=source_task_id,
        )

        runtime.ensure_source_task_exists()
        runtime.ensure_completed_source_task()

        task_json = runtime.load_source_task_json()
        state_json = runtime.load_source_state_json()
        cycle = int(state_json["cycle"])

        role_definition = runtime.read_role_definition()
        template = runtime.read_template()
        output_schema = runtime.read_schema_text()
        output_json_path = runtime.get_report_path(cycle)

        reports_text = runtime.load_source_reports_text(cycle)
        task_list_summary = runtime.build_task_list_summary()
        reference_docs = runtime.build_reference_docs_text(reference_doc_paths)

        prompt_text = self._build_prompt(
            source_task_id=source_task_id,
            cycle=cycle,
            repo_path=str(target_repo),
            role_definition=role_definition,
            template=template,
            task_json=task_json,
            state_json=state_json,
            implementer_report_json=reports_text["implementer_report_json"],
            reviewer_report_json=reports_text["reviewer_report_json"],
            director_report_json=reports_text["director_report_json"],
            task_list_summary=task_list_summary,
            reference_docs=reference_docs,
            output_schema=output_schema,
            output_json_path=output_json_path,
        )

        prompt_path = runtime.write_prompt(cycle=cycle, content=prompt_text)

        claude_result = run_claude_print_mode(
            repo_path=repo_path,
            prompt_text=prompt_text,
        )
        if claude_result.returncode != 0:
            raise RuntimeError(
                "claude command failed while generating planner proposals. "
                f"returncode={claude_result.returncode}"
            )

        if not output_json_path.exists():
            raise FileNotFoundError(f"Planner report file not found: {output_json_path}")

        with output_json_path.open("r", encoding="utf-8") as f:
            planner_report = json.load(f)

        SchemaValidator(runtime.schemas_dir).validate_report(
            role="planner",
            data=planner_report,
        )
        self._check_identity(
            expected_source_task_id=source_task_id,
            expected_cycle=cycle,
            report=planner_report,
        )

        return {
            "source_task_id": source_task_id,
            "cycle": cycle,
            "prompt_path": str(prompt_path),
            "output_json_path": str(output_json_path),
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
        role_definition: str,
        template: str,
        task_json: dict,
        state_json: dict,
        implementer_report_json: str,
        reviewer_report_json: str,
        director_report_json: str,
        task_list_summary: str,
        reference_docs: str,
        output_schema: str,
        output_json_path: Path,
    ) -> str:
        task_json_text = json.dumps(task_json, indent=2, ensure_ascii=False)
        state_json_text = json.dumps(state_json, indent=2, ensure_ascii=False)

        return render_prompt(
            template,
            role_definition=role_definition,
            task_json=task_json_text,
            state_json=state_json_text,
            implementer_report_json=implementer_report_json,
            reviewer_report_json=reviewer_report_json,
            director_report_json=director_report_json,
            task_list_summary=task_list_summary,
            reference_docs=reference_docs,
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

        if str(report.get("role")) != "planner":
            raise ValueError(
                f"role mismatch: expected=planner, actual={report.get('role')}"
            )

        if int(report.get("cycle")) != int(expected_cycle):
            raise ValueError(
                f"cycle mismatch: expected={expected_cycle}, actual={report.get('cycle')}"
            )
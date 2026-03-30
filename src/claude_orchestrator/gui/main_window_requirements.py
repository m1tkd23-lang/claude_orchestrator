# src\claude_orchestrator\gui\main_window_requirements.py
from __future__ import annotations

import json
from pathlib import Path

from PySide6.QtCore import QThread

from claude_orchestrator.application.usecases.create_task_usecase import (
    CreateTaskUseCase,
)
from claude_orchestrator.application.usecases.generate_requirements_docs_usecase import (
    GenerateRequirementsDocsUseCase,
)
from claude_orchestrator.application.usecases.load_requirements_usecase import (
    LoadRequirementsUseCase,
)
from claude_orchestrator.application.usecases.run_requirements_refinement_loop_usecase import (
    RunRequirementsRefinementLoopUseCase,
)
from claude_orchestrator.application.usecases.save_requirements_usecase import (
    SaveRequirementsUseCase,
)
from claude_orchestrator.application.usecases.validate_requirements_usecase import (
    ValidateRequirementsUseCase,
)
from claude_orchestrator.gui.dialog_helpers import append_log, show_error, show_info
from claude_orchestrator.gui.requirements_claude_worker import (
    RequirementsClaudeWorker,
    RequirementsClaudeWorkerResult,
)
from claude_orchestrator.gui.services.requirements_prompt_service import (
    build_requirements_authoring_prompt,
)
from claude_orchestrator.gui.state_helpers import (
    handle_repo_changed,
    parse_multiline_list,
    require_repo_path,
)


class MainWindowRequirementsMixin:
    def _reset_requirements_view(self) -> None:
        if hasattr(self, "requirements_path_edit"):
            self.requirements_path_edit.clear()
        if hasattr(self, "requirements_schema_path_edit"):
            self.requirements_schema_path_edit.clear()
        if hasattr(self, "requirements_status_edit"):
            self.requirements_status_edit.setText("idle")
        if hasattr(self, "requirements_json_edit"):
            self.requirements_json_edit.clear()
        if hasattr(self, "requirements_open_questions_edit"):
            self.requirements_open_questions_edit.clear()
        if hasattr(self, "requirements_change_log_edit"):
            self.requirements_change_log_edit.clear()
        if hasattr(self, "requirements_validation_result_edit"):
            self.requirements_validation_result_edit.clear()
        if hasattr(self, "requirements_change_summary_edit"):
            self.requirements_change_summary_edit.clear()
        if hasattr(self, "requirements_change_details_edit"):
            self.requirements_change_details_edit.clear()
        if hasattr(self, "requirements_ai_request_edit"):
            self.requirements_ai_request_edit.clear()
        if hasattr(self, "requirements_ai_response_edit"):
            self.requirements_ai_response_edit.clear()
        self._set_requirements_claude_busy(False)

    def _set_requirements_status(self, text: str) -> None:
        self.requirements_status_edit.setText(text)

    def _set_requirements_validation_result(self, text: str) -> None:
        self.requirements_validation_result_edit.setPlainText(text)

    def _set_requirements_json_text(self, payload: dict) -> None:
        self.requirements_json_edit.setPlainText(
            json.dumps(payload, ensure_ascii=False, indent=2)
        )

    def _set_requirements_support_views(
        self,
        *,
        open_questions: dict | None,
        change_log: dict | None,
    ) -> None:
        self.requirements_open_questions_edit.setPlainText(
            json.dumps(open_questions or {}, ensure_ascii=False, indent=2)
        )
        self.requirements_change_log_edit.setPlainText(
            json.dumps(change_log or {}, ensure_ascii=False, indent=2)
        )

    def _collect_requirements_json_from_editor(self) -> dict:
        raw_text = self.requirements_json_edit.toPlainText().strip()
        if not raw_text:
            raise ValueError("requirements.json editor is empty.")

        try:
            payload = json.loads(raw_text)
        except json.JSONDecodeError as exc:
            raise ValueError(f"requirements.json is not valid JSON: {exc}") from exc

        if not isinstance(payload, dict):
            raise ValueError("requirements.json root must be an object.")
        return payload

    def _collect_requirements_ai_json_from_editor(self) -> dict:
        raw_text = self.requirements_ai_response_edit.toPlainText().strip()
        if not raw_text:
            raise ValueError("Claude提案JSON が空です。")

        try:
            payload = json.loads(raw_text)
        except json.JSONDecodeError as exc:
            raise ValueError(f"Claude提案JSON is not valid JSON: {exc}") from exc

        if not isinstance(payload, dict):
            raise ValueError("Claude提案JSON root must be an object.")
        return payload

    def _set_requirements_claude_busy(self, busy: bool) -> None:
        if hasattr(self, "btn_requirements_claude_suggest"):
            self.btn_requirements_claude_suggest.setEnabled(not busy)
        if hasattr(self, "btn_requirements_apply_claude_json"):
            self.btn_requirements_apply_claude_json.setEnabled(not busy)
        if hasattr(self, "btn_load_requirements"):
            self.btn_load_requirements.setEnabled(not busy)
        if hasattr(self, "btn_validate_requirements"):
            self.btn_validate_requirements.setEnabled(not busy)
        if hasattr(self, "btn_save_requirements"):
            self.btn_save_requirements.setEnabled(not busy)
        if hasattr(self, "btn_generate_requirements_docs"):
            self.btn_generate_requirements_docs.setEnabled(not busy)
        if hasattr(self, "btn_run_requirements_refinement_loop"):
            self.btn_run_requirements_refinement_loop.setEnabled(not busy)
        if hasattr(self, "btn_create_task_from_requirements"):
            self.btn_create_task_from_requirements.setEnabled(not busy)

    def on_load_requirements(self) -> None:
        try:
            repo_path = require_repo_path(self)
            handle_repo_changed(self, repo_path)

            result = LoadRequirementsUseCase().execute(repo_path=repo_path)
            self.requirements_path_edit.setText(result["requirements_path"])
            schema_path = (
                Path(repo_path).resolve()
                / ".claude_orchestrator"
                / "schemas"
                / "requirements.schema.json"
            )
            self.requirements_schema_path_edit.setText(str(schema_path))

            if result["errors"]:
                self._set_requirements_status("load_error")
                self._set_requirements_validation_result(
                    "\n".join(f"- {err}" for err in result["errors"])
                )
                return

            self._set_requirements_json_text(result["requirements"] or {})
            self._set_requirements_support_views(
                open_questions=result.get("open_questions"),
                change_log=result.get("change_log"),
            )

            requirements = result.get("requirements") or {}
            requirement_status = str(requirements.get("requirement_status", "")).strip()
            self._set_requirements_status(requirement_status or "loaded")
            self._set_requirements_validation_result("読込成功")
            append_log(
                self,
                f"[INFO] requirements loaded: {result['requirements_path']}",
            )
        except Exception as exc:
            show_error(self, "requirements 読込エラー", exc)

    def on_validate_requirements(self) -> None:
        try:
            repo_path = require_repo_path(self)
            handle_repo_changed(self, repo_path)

            payload = self._collect_requirements_json_from_editor()
            result = ValidateRequirementsUseCase().execute(
                repo_path=repo_path,
                requirements_json=payload,
            )

            self.requirements_path_edit.setText(result["requirements_path"])
            self.requirements_schema_path_edit.setText(result["schema_path"])

            if result["errors"]:
                self._set_requirements_status("invalid")
                self._set_requirements_validation_result(
                    "\n".join(f"- {err}" for err in result["errors"])
                )
                append_log(self, "[WARN] requirements validation failed")
                return

            requirement_status = str(payload.get("requirement_status", "")).strip()
            self._set_requirements_status(requirement_status or "valid")
            self._set_requirements_validation_result("検証成功")
            append_log(self, "[INFO] requirements validated")
        except Exception as exc:
            show_error(self, "requirements 検証エラー", exc)

    def on_save_requirements(self) -> None:
        try:
            repo_path = require_repo_path(self)
            handle_repo_changed(self, repo_path)

            payload = self._collect_requirements_json_from_editor()
            change_summary = self.requirements_change_summary_edit.text().strip() or None
            change_details = parse_multiline_list(
                self.requirements_change_details_edit.toPlainText()
            )

            result = SaveRequirementsUseCase().execute(
                repo_path=repo_path,
                requirements_json=payload,
                changed_by="gui",
                change_summary=change_summary,
                change_details=change_details or None,
            )

            self.requirements_path_edit.setText(result["requirements_path"])
            self.requirements_schema_path_edit.setText(result["schema_path"])

            if result["errors"]:
                self._set_requirements_status("save_error")
                self._set_requirements_validation_result(
                    "\n".join(f"- {err}" for err in result["errors"])
                )
                append_log(self, "[WARN] requirements save rejected by validation")
                return

            requirement_status = str(payload.get("requirement_status", "")).strip()
            self._set_requirements_status(requirement_status or "saved")
            self._set_requirements_validation_result(
                f"保存成功\nupdated_at: {result['updated_at']}"
            )

            load_result = LoadRequirementsUseCase().execute(repo_path=repo_path)
            if load_result["ok"]:
                self._set_requirements_support_views(
                    open_questions=load_result.get("open_questions"),
                    change_log=load_result.get("change_log"),
                )

            append_log(
                self,
                f"[INFO] requirements saved: {result['requirements_path']}",
            )
            show_info(self, "requirements 保存完了", result["requirements_path"])
        except Exception as exc:
            show_error(self, "requirements 保存エラー", exc)

    def on_generate_requirements_docs(self) -> None:
        try:
            repo_path = require_repo_path(self)
            handle_repo_changed(self, repo_path)

            result = GenerateRequirementsDocsUseCase().execute(repo_path=repo_path)

            self.requirements_schema_path_edit.setText(result["schema_path"])

            if result["errors"]:
                self._set_requirements_status("docs_error")
                self._set_requirements_validation_result(
                    "\n".join(f"- {err}" for err in result["errors"])
                )
                append_log(self, "[WARN] requirements docs generation failed")
                return

            self._set_requirements_status("docs_generated")
            lines = ["docs生成成功"]
            for item in result["written_files"]:
                lines.append(f"- {item['path']}")
            self._set_requirements_validation_result("\n".join(lines))

            append_log(self, "[INFO] requirements docs generated")
            show_info(
                self,
                "requirements docs 生成完了",
                "\n".join(item["path"] for item in result["written_files"]),
            )
        except Exception as exc:
            show_error(self, "requirements docs生成エラー", exc)

    def on_requirements_claude_suggest(self) -> None:
        try:
            repo_path = require_repo_path(self)
            handle_repo_changed(self, repo_path)

            payload = self._collect_requirements_json_from_editor()
            user_request = self.requirements_ai_request_edit.toPlainText().strip()
            if not user_request:
                raise ValueError("Claudeへの依頼内容を入力してください。")

            schema_path = (
                Path(repo_path).resolve()
                / ".claude_orchestrator"
                / "schemas"
                / "requirements.schema.json"
            )
            if not schema_path.exists():
                raise FileNotFoundError(f"Schema not found: {schema_path}")

            schema_text = schema_path.read_text(encoding="utf-8")
            prompt_text = build_requirements_authoring_prompt(
                repo_path=repo_path,
                requirements_json=payload,
                user_request=user_request,
                schema_text=schema_text,
            )

            self.requirements_ai_response_edit.clear()
            self._set_requirements_status("claude_running")
            self._set_requirements_validation_result("Claude に要件整理を依頼中...")
            self._set_requirements_claude_busy(True)

            self._requirements_claude_thread = QThread(self)
            self._requirements_claude_worker = RequirementsClaudeWorker(
                repo_path=repo_path,
                prompt_text=prompt_text,
                timeout_seconds=300,
            )
            self._requirements_claude_worker.moveToThread(
                self._requirements_claude_thread
            )

            self._requirements_claude_thread.started.connect(
                self._requirements_claude_worker.run
            )
            self._requirements_claude_worker.result_ready.connect(
                self._on_requirements_claude_result
            )
            self._requirements_claude_worker.log_message.connect(
                lambda message: append_log(self, message)
            )
            self._requirements_claude_worker.error_signal.connect(
                self._on_requirements_claude_error
            )
            self._requirements_claude_worker.finished.connect(
                self._requirements_claude_thread.quit
            )
            self._requirements_claude_worker.finished.connect(
                self._requirements_claude_worker.deleteLater
            )
            self._requirements_claude_thread.finished.connect(
                self._requirements_claude_thread.deleteLater
            )
            self._requirements_claude_thread.finished.connect(
                self._on_requirements_claude_finished
            )

            self._requirements_claude_thread.start()
        except Exception as exc:
            self._set_requirements_claude_busy(False)
            show_error(self, "requirements Claude 実行エラー", exc)

    def on_apply_requirements_claude_json(self) -> None:
        try:
            repo_path = require_repo_path(self)
            handle_repo_changed(self, repo_path)

            payload = self._collect_requirements_ai_json_from_editor()
            validation = ValidateRequirementsUseCase().execute(
                repo_path=repo_path,
                requirements_json=payload,
            )
            if validation["errors"]:
                self._set_requirements_status("claude_invalid")
                self._set_requirements_validation_result(
                    "\n".join(
                        ["Claude提案JSONは schema に適合しません。"]
                        + [f"- {err}" for err in validation["errors"]]
                    )
                )
                append_log(self, "[WARN] Claude suggestion rejected by validation")
                return

            self._set_requirements_json_text(payload)
            requirement_status = str(payload.get("requirement_status", "")).strip()
            self._set_requirements_status(requirement_status or "claude_applied")
            self._set_requirements_validation_result(
                "Claude提案JSONを requirements editor に反映しました。"
            )
            append_log(self, "[INFO] Claude suggestion applied to requirements editor")
        except Exception as exc:
            show_error(self, "Claude提案反映エラー", exc)

    def on_run_requirements_refinement_loop(self) -> None:
        try:
            repo_path = require_repo_path(self)
            handle_repo_changed(self, repo_path)

            self._set_requirements_status("refinement_running")
            self._set_requirements_validation_result("要件改善ループ実行中...")

            result = RunRequirementsRefinementLoopUseCase().execute(repo_path=repo_path)

            log_lines: list[str] = []
            for log in result["logs"]:
                if log["phase"] == "review":
                    log_lines.append(
                        f"[review] iter={log['iteration']} "
                        f"critical={log['critical']} "
                        f"major={log['major']} "
                        f"decision={log['decision']}"
                    )
                elif log["phase"] == "refine":
                    log_lines.append(
                        f"[refine] iter={log['iteration']} "
                        f"path={log.get('write_path', '')}"
                    )

            if result["ok"]:
                self._set_requirements_status("refinement_completed")
                log_lines.append("✔ COMPLETED")
            else:
                self._set_requirements_status("refinement_max_reached")
                log_lines.append("⚠ MAX ITERATION")

            self._set_requirements_validation_result("\n".join(log_lines))
            append_log(self, "[INFO] requirements refinement completed")

            self.on_load_requirements()
        except Exception as exc:
            show_error(self, "requirements refinement エラー", exc)

    def on_create_task_from_requirements(self) -> None:
        try:
            repo_path = require_repo_path(self)
            handle_repo_changed(self, repo_path)

            docs_result = GenerateRequirementsDocsUseCase().execute(repo_path=repo_path)
            if docs_result["errors"]:
                raise ValueError(
                    "requirements docs 生成に失敗しました。\n"
                    + "\n".join(docs_result["errors"])
                )

            payload = self._collect_requirements_json_from_editor()

            project_name = str(payload.get("project_name", "")).strip() or "新規プロジェクト"
            product_summary = str(payload.get("product_summary", "")).strip()
            core_purpose = str(payload.get("core_purpose", "")).strip()
            priority_order = payload.get("priority_order", [])

            title = "初期要件docsを確認し次の安全な実装taskを定義する"

            description_lines: list[str] = [
                "このtaskの目的は、requirements から生成された主要docsを確認し、",
                "completion_definition に対する未達項目と feature_inventory の未実装項目を照合した上で、",
                "次に着手すべき安全な実装taskを定義することである。",
                "",
                "今回のtaskでは以下を行うこと:",
                "- context_files の3文書を確認する",
                "- 何を作るか、何が完成か、何が未実装かを整理する",
                "- 最初に着手すべき task を1件または少数件に絞る",
                "- 大きすぎる task は分解する",
                "- いきなり全体実装には着手しない",
                "",
                f"project_name: {project_name}",
            ]

            if product_summary:
                description_lines.append(f"product_summary: {product_summary}")
            if core_purpose:
                description_lines.append(f"core_purpose: {core_purpose}")

            if isinstance(priority_order, list):
                normalized_priority_order = [
                    str(item).strip() for item in priority_order if str(item).strip()
                ]
                if normalized_priority_order:
                    description_lines.append("")
                    description_lines.append("priority_order:")
                    description_lines.extend(f"- {item}" for item in normalized_priority_order)

            description = "\n".join(description_lines).strip()

            context_files = [
                ".claude_orchestrator/docs/project_core/開発の目的本筋.md",
                ".claude_orchestrator/docs/completion_definition.md",
                ".claude_orchestrator/docs/feature_inventory.md",
            ]

            requirements_constraints = payload.get("constraints", [])
            normalized_constraints = [
                str(item).strip()
                for item in requirements_constraints
                if str(item).strip()
            ]

            normalized_constraints.extend(
                [
                    "初回taskでは全体実装に直接着手しないこと",
                    "context_files の3文書を根拠に次taskを定義すること",
                    "大きすぎるtaskは分解すること",
                    "feature_inventory と completion_definition の整合を確認してから提案すること",
                ]
            )

            task_dir = CreateTaskUseCase().execute(
                repo_path=repo_path,
                title=title,
                description=description,
                context_files=context_files,
                constraints=normalized_constraints,
            )

            append_log(
                self,
                f"[INFO] task created from requirements: {task_dir}",
            )
            show_info(self, "タスク生成", str(task_dir))
        except Exception as exc:
            show_error(self, "task作成エラー", exc)

    def _on_requirements_claude_result(
        self,
        result: RequirementsClaudeWorkerResult,
    ) -> None:
        try:
            self.requirements_ai_response_edit.setPlainText(
                json.dumps(
                    result.suggested_requirements_json,
                    ensure_ascii=False,
                    indent=2,
                )
            )

            repo_path = require_repo_path(self)
            validation = ValidateRequirementsUseCase().execute(
                repo_path=repo_path,
                requirements_json=result.suggested_requirements_json,
            )

            if validation["errors"]:
                self._set_requirements_status("claude_invalid")
                self._set_requirements_validation_result(
                    "\n".join(
                        ["Claude提案JSON受信（schema不適合）"]
                        + [f"- {err}" for err in validation["errors"]]
                    )
                )
                append_log(self, "[WARN] Claude suggestion received but invalid")
                return

            self._set_requirements_status("claude_ready")
            self._set_requirements_validation_result(
                "Claude提案JSON受信（schema適合）\n"
                "内容を確認し、問題なければ「AI提案をeditorへ反映」を押してください。"
            )
            append_log(self, "[INFO] Claude suggestion received and validated")
        except Exception as exc:
            show_error(self, "Claude提案受信処理エラー", exc)

    def _on_requirements_claude_error(self, title: str, message: str) -> None:
        self._set_requirements_status("claude_error")
        self._set_requirements_validation_result(message)
        append_log(self, f"[ERROR] {message}")
        show_error(self, title, RuntimeError(message))

    def _on_requirements_claude_finished(self) -> None:
        self._set_requirements_claude_busy(False)
        self._requirements_claude_thread = None
        self._requirements_claude_worker = None
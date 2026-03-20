# src\claude_orchestrator\gui\planner_worker.py
from __future__ import annotations

from PySide6.QtCore import QObject, Signal

from claude_orchestrator.application.usecases.generate_next_task_proposals_usecase import (
    GenerateNextTaskProposalsUseCase,
)


class PlannerWorker(QObject):
    result_ready = Signal(object)
    log_message = Signal(str)
    error_signal = Signal(str, str)
    finished = Signal()

    def __init__(
        self,
        *,
        repo_path: str,
        source_task_id: str,
        reference_doc_paths: list[str] | None = None,
    ) -> None:
        super().__init__()
        self.repo_path = repo_path
        self.source_task_id = source_task_id
        self.reference_doc_paths = reference_doc_paths or []

    def run(self) -> None:
        try:
            self.log_message.emit(
                f"[INFO] planner generation started: source_task_id={self.source_task_id}"
            )
            result = GenerateNextTaskProposalsUseCase().execute(
                repo_path=self.repo_path,
                source_task_id=self.source_task_id,
                reference_doc_paths=self.reference_doc_paths,
            )
            self.result_ready.emit(result)
            self.log_message.emit(
                f"[INFO] planner generation completed: source_task_id={self.source_task_id}"
            )
        except Exception as exc:
            self.error_signal.emit(
                "次タスク案作成エラー",
                f"{type(exc).__name__}: {exc}",
            )
        finally:
            self.finished.emit()
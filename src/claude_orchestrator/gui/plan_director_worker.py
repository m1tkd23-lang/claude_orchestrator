# src\claude_orchestrator\gui\plan_director_worker.py
from __future__ import annotations

from PySide6.QtCore import QObject, Signal

from claude_orchestrator.application.usecases.run_plan_director_usecase import (
    RunPlanDirectorUseCase,
)


class PlanDirectorWorker(QObject):
    result_ready = Signal(object)
    log_message = Signal(str)
    error_signal = Signal(str, str)
    finished = Signal()

    def __init__(self, *, repo_path: str, source_task_id: str) -> None:
        super().__init__()
        self.repo_path = repo_path
        self.source_task_id = source_task_id

    def run(self) -> None:
        try:
            self.log_message.emit(
                "[INFO] plan_director started: "
                f"source_task_id={self.source_task_id}"
            )
            result = RunPlanDirectorUseCase().execute(
                repo_path=self.repo_path,
                source_task_id=self.source_task_id,
            )
            self.result_ready.emit(result)
            self.log_message.emit(
                "[INFO] plan_director completed: "
                f"source_task_id={self.source_task_id}"
            )
        except Exception as exc:
            self.error_signal.emit(
                "plan_director 実行エラー",
                f"{type(exc).__name__}: {exc}",
            )
        finally:
            self.finished.emit()
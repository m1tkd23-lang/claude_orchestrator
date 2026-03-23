# src\claude_orchestrator\gui\auto_run_worker.py
from __future__ import annotations

from PySide6.QtCore import QObject, Signal

from claude_orchestrator.application.usecases.run_task_usecase import RunTaskUseCase


class AutoRunWorker(QObject):
    status_changed = Signal(str, str, str, str)
    monitor_message = Signal(str)
    log_message = Signal(str)
    show_next_ready = Signal(object)
    validation_ready = Signal(str)
    task_detail_requested = Signal(str)
    task_list_refresh_requested = Signal()
    error_signal = Signal(str, str)
    completed_signal = Signal(str, str, str)
    finished = Signal()

    def __init__(self, *, repo_path: str, task_id: str) -> None:
        super().__init__()
        self.repo_path = repo_path
        self.task_id = task_id

    def run(self) -> None:
        try:
            RunTaskUseCase().execute(
                repo_path=self.repo_path,
                task_id=self.task_id,
                event_callback=self._handle_event,
            )
        except Exception as exc:
            self.error_signal.emit("Claude自動実行エラー", f"{type(exc).__name__}: {exc}")
        finally:
            self.finished.emit()

    def _handle_event(self, event: dict) -> None:
        event_type = str(event.get("type", "")).strip()

        if event_type == "status_changed":
            self.status_changed.emit(
                str(event.get("status", "")),
                str(event.get("step", "")),
                str(event.get("role", "")),
                str(event.get("cycle", "")),
            )
            return

        if event_type == "monitor_message":
            self.monitor_message.emit(str(event.get("message", "")))
            return

        if event_type == "log_message":
            self.log_message.emit(str(event.get("message", "")))
            return

        if event_type == "show_next_ready":
            self.show_next_ready.emit(event.get("result"))
            return

        if event_type == "validation_ready":
            self.validation_ready.emit(str(event.get("text", "")))
            return

        if event_type == "task_detail_requested":
            self.task_detail_requested.emit(str(event.get("task_id", self.task_id)))
            return

        if event_type == "task_list_refresh_requested":
            self.task_list_refresh_requested.emit()
            return

        if event_type == "task_completed":
            self.completed_signal.emit(
                str(event.get("task_id", self.task_id)),
                str(event.get("cycle", "")),
                str(event.get("status", "")),
            )
            return
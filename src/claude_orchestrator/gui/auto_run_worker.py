# src\claude_orchestrator\gui\auto_run_worker.py
from __future__ import annotations

from pathlib import Path

from PySide6.QtCore import QObject, Signal

from claude_orchestrator.application.usecases.advance_task_usecase import (
    AdvanceTaskUseCase,
)
from claude_orchestrator.application.usecases.show_next_usecase import (
    ShowNextUseCase,
)
from claude_orchestrator.application.usecases.validate_report_usecase import (
    ValidateReportUseCase,
)
from claude_orchestrator.gui.claude_runner import run_claude_print_mode
from claude_orchestrator.infrastructure.task_runtime import TaskRuntime


class AutoRunWorker(QObject):
    status_changed = Signal(str, str, str, str)
    monitor_message = Signal(str)
    log_message = Signal(str)
    show_next_ready = Signal(object)
    validation_ready = Signal(str)
    task_detail_requested = Signal(str)
    task_list_refresh_requested = Signal()
    error_signal = Signal(str, str)
    completed_signal = Signal(str, str)
    finished = Signal()

    def __init__(self, *, repo_path: str, task_id: str) -> None:
        super().__init__()
        self.repo_path = repo_path
        self.task_id = task_id

    def run(self) -> None:
        try:
            runtime = TaskRuntime(
                target_repo=Path(self.repo_path).resolve(),
                task_id=self.task_id,
            )
            initial_state = runtime.load_state_json()
            initial_next_role = str(initial_state.get("next_role", ""))
            initial_cycle = str(initial_state.get("cycle", ""))

            if initial_next_role == "none":
                self.status_changed.emit("completed", "idle", "none", initial_cycle)
                self.monitor_message.emit("completed")
                self.log_message.emit(
                    f"[INFO] task already completed: {self.task_id}"
                )
                self.completed_signal.emit(self.task_id, initial_cycle)
                return

            self.status_changed.emit(
                "running",
                "starting",
                initial_next_role,
                initial_cycle,
            )
            self.monitor_message.emit("process started")
            self.monitor_message.emit(f"role / cycle: {initial_next_role} / {initial_cycle}")
            self.monitor_message.emit(f"cwd: {Path(self.repo_path).resolve()}")
            self.log_message.emit(f"[INFO] auto run started: task_id={self.task_id}")

            while True:
                advance_result = self._run_single_cycle_step()
                next_role = str(advance_result["next_role"])
                cycle = str(advance_result["cycle"])
                status = str(advance_result["status"])

                if next_role == "none" or status == "completed":
                    self.status_changed.emit("completed", "stopped", "none", cycle)
                    self.monitor_message.emit("completed")
                    self.log_message.emit(
                        f"[INFO] auto run completed: task_id={self.task_id}, cycle={cycle}"
                    )
                    self.completed_signal.emit(self.task_id, cycle)
                    break

                self.status_changed.emit("running", "next role ready", next_role, cycle)
                self.monitor_message.emit(
                    f"advanced to next role: {next_role} (cycle={cycle})"
                )

        except Exception as exc:
            self.error_signal.emit("Claude自動実行エラー", f"{type(exc).__name__}: {exc}")
        finally:
            self.finished.emit()

    def _run_single_cycle_step(self) -> dict:
        self.status_changed.emit("running", "show-next", "", "")
        show_next_result = ShowNextUseCase().execute(
            repo_path=self.repo_path,
            task_id=self.task_id,
        )
        self.show_next_ready.emit(show_next_result)

        role = str(show_next_result["role"])
        cycle = str(show_next_result["cycle"])
        prompt_path = str(show_next_result["prompt_path"])
        output_json_path = str(show_next_result["output_json_path"])

        self.status_changed.emit("running", "show-next", role, cycle)
        self.monitor_message.emit(f"show-next completed")
        self.monitor_message.emit(f"role / cycle: {role} / {cycle}")
        self.log_message.emit(
            "[INFO] show-next completed: "
            f"task_id={self.task_id}, role={role}, cycle={cycle}"
        )

        prompt_text = Path(prompt_path).read_text(encoding="utf-8")
        if not prompt_text.strip():
            raise ValueError("prompt text is empty.")

        self.status_changed.emit("running", "claude", role, cycle)
        self.monitor_message.emit("process started")
        self.monitor_message.emit(f"cwd: {Path(self.repo_path).resolve()}")
        self.log_message.emit(
            "[INFO] claude step started: "
            f"task_id={self.task_id}, role={role}, cycle={cycle}"
        )
        self.log_message.emit(f"[INFO] claude cwd: {Path(self.repo_path).resolve()}")

        claude_result = run_claude_print_mode(
            repo_path=self.repo_path,
            prompt_text=prompt_text,
        )

        self.log_message.emit(
            "[INFO] claude finished: "
            f"returncode={claude_result.returncode}, "
            f"command={' '.join(claude_result.command)}"
        )

        stdout_text = claude_result.stdout.strip()
        stderr_text = claude_result.stderr.strip()

        if stdout_text:
            self.monitor_message.emit("stdout")
            self.monitor_message.emit(stdout_text)
            self.log_message.emit("[INFO] claude stdout:")
            self.log_message.emit(stdout_text)

        if stderr_text:
            self.monitor_message.emit("stderr")
            self.monitor_message.emit(stderr_text)
            self.log_message.emit("[INFO] claude stderr:")
            self.log_message.emit(stderr_text)

        if claude_result.returncode != 0:
            raise RuntimeError(
                "claude command failed. "
                f"returncode={claude_result.returncode}"
            )

        if not Path(output_json_path).exists():
            raise FileNotFoundError(f"Report file not found: {output_json_path}")

        self.monitor_message.emit("report file detected")
        self.log_message.emit(f"[INFO] report json saved: {output_json_path}")

        self.status_changed.emit("running", "validate-report", role, cycle)
        validate_result = ValidateReportUseCase().execute(
            repo_path=self.repo_path,
            task_id=self.task_id,
            role=role,
        )
        validation_text = (
            f"valid: {validate_result['valid']}\n"
            f"role: {validate_result['role']}\n"
            f"cycle: {validate_result['cycle']}\n"
            f"report_path: {validate_result['report_path']}"
        )
        self.validation_ready.emit(validation_text)
        self.monitor_message.emit("validate success")
        self.log_message.emit(
            "[INFO] validate-report success: "
            f"task_id={self.task_id}, role={validate_result['role']}, cycle={validate_result['cycle']}"
        )

        self.status_changed.emit("running", "advance", role, cycle)
        advance_result = AdvanceTaskUseCase().execute(
            repo_path=self.repo_path,
            task_id=self.task_id,
        )
        self.monitor_message.emit(
            "advanced to next role: "
            f"{advance_result['next_role']} (status={advance_result['status']}, cycle={advance_result['cycle']})"
        )
        self.log_message.emit(
            "[INFO] advance completed: "
            f"task_id={self.task_id}, "
            f"status={advance_result['status']}, "
            f"current={advance_result['current_stage']}, "
            f"next={advance_result['next_role']}, "
            f"cycle={advance_result['cycle']}"
        )

        self.task_detail_requested.emit(self.task_id)
        self.task_list_refresh_requested.emit()

        return advance_result
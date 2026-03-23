# src\claude_orchestrator\application\usecases\run_task_usecase.py
from __future__ import annotations

from pathlib import Path
from typing import Callable

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
from claude_orchestrator.infrastructure.task_execution_lock import (
    TaskExecutionLock,
    TaskExecutionOwner,
)
from claude_orchestrator.infrastructure.task_runtime import TaskRuntime

RunTaskEventCallback = Callable[[dict], None]


class RunTaskUseCase:
    def execute(
        self,
        *,
        repo_path: str,
        task_id: str,
        event_callback: RunTaskEventCallback | None = None,
        executor_type: str | None = None,
        executor_id: str | None = None,
        executor_label: str | None = None,
    ) -> dict:
        resolved_repo_path = str(Path(repo_path).resolve())
        runtime = TaskRuntime(
            target_repo=Path(resolved_repo_path),
            task_id=task_id,
        )
        owner = TaskExecutionOwner.normalize(
            executor_type=executor_type,
            executor_id=executor_id,
            executor_label=executor_label,
        )
        execution_lock = TaskExecutionLock(
            repo_path=resolved_repo_path,
            task_id=task_id,
        )
        execution_lock.acquire(owner=owner)

        try:
            self._emit(
                event_callback,
                {
                    "type": "log_message",
                    "message": (
                        "[INFO] execution lock acquired: "
                        f"task_id={task_id}, "
                        f"owner_type={owner.owner_type}, "
                        f"owner_id={owner.owner_id}"
                    ),
                },
            )

            initial_state = runtime.load_state_json()
            initial_next_role = str(initial_state.get("next_role", ""))
            initial_cycle = str(initial_state.get("cycle", ""))

            if initial_next_role == "none":
                self._emit(
                    event_callback,
                    {
                        "type": "status_changed",
                        "status": "completed",
                        "step": "idle",
                        "role": "none",
                        "cycle": initial_cycle,
                    },
                )
                self._emit(
                    event_callback,
                    {
                        "type": "monitor_message",
                        "message": "completed",
                    },
                )
                self._emit(
                    event_callback,
                    {
                        "type": "log_message",
                        "message": f"[INFO] task already completed: {task_id}",
                    },
                )
                self._emit(
                    event_callback,
                    {
                        "type": "task_completed",
                        "task_id": task_id,
                        "cycle": initial_cycle,
                        "status": "completed",
                    },
                )
                return {
                    "task_id": task_id,
                    "status": "completed",
                    "cycle": int(initial_state.get("cycle", 1)),
                    "current_stage": str(initial_state.get("current_stage", "")),
                    "next_role": "none",
                    "state_path": str(runtime.state_json_path),
                }

            self._emit(
                event_callback,
                {
                    "type": "status_changed",
                    "status": "running",
                    "step": "starting",
                    "role": initial_next_role,
                    "cycle": initial_cycle,
                },
            )
            self._emit(
                event_callback,
                {
                    "type": "monitor_message",
                    "message": "process started",
                },
            )
            self._emit(
                event_callback,
                {
                    "type": "monitor_message",
                    "message": f"role / cycle: {initial_next_role} / {initial_cycle}",
                },
            )
            self._emit(
                event_callback,
                {
                    "type": "monitor_message",
                    "message": f"cwd: {resolved_repo_path}",
                },
            )
            self._emit(
                event_callback,
                {
                    "type": "log_message",
                    "message": (
                        "[INFO] auto run started: "
                        f"task_id={task_id}, owner={owner.owner_label}"
                    ),
                },
            )

            last_advance_result: dict | None = None

            while True:
                advance_result = self._run_single_cycle_step(
                    repo_path=resolved_repo_path,
                    task_id=task_id,
                    event_callback=event_callback,
                )
                last_advance_result = advance_result

                next_role = str(advance_result["next_role"])
                cycle = str(advance_result["cycle"])
                status = str(advance_result["status"])

                if next_role == "none" or status in {"completed", "blocked", "stopped"}:
                    final_ui_status = "completed" if status == "completed" else "stopped"
                    self._emit(
                        event_callback,
                        {
                            "type": "status_changed",
                            "status": final_ui_status,
                            "step": "stopped",
                            "role": "none",
                            "cycle": cycle,
                        },
                    )
                    self._emit(
                        event_callback,
                        {
                            "type": "monitor_message",
                            "message": "completed" if status == "completed" else status,
                        },
                    )
                    self._emit(
                        event_callback,
                        {
                            "type": "log_message",
                            "message": (
                                "[INFO] auto run finished: "
                                f"task_id={task_id}, status={status}, cycle={cycle}"
                            ),
                        },
                    )
                    self._emit(
                        event_callback,
                        {
                            "type": "task_completed",
                            "task_id": task_id,
                            "cycle": cycle,
                            "status": status,
                        },
                    )
                    return advance_result

                self._emit(
                    event_callback,
                    {
                        "type": "status_changed",
                        "status": "running",
                        "step": "next role ready",
                        "role": next_role,
                        "cycle": cycle,
                    },
                )
                self._emit(
                    event_callback,
                    {
                        "type": "monitor_message",
                        "message": f"advanced to next role: {next_role} (cycle={cycle})",
                    },
                )

            return last_advance_result or {
                "task_id": task_id,
                "status": "stopped",
                "cycle": int(initial_state.get("cycle", 1)),
                "current_stage": str(initial_state.get("current_stage", "")),
                "next_role": str(initial_state.get("next_role", "")),
                "state_path": str(runtime.state_json_path),
            }
        finally:
            execution_lock.release(owner=owner)
            self._emit(
                event_callback,
                {
                    "type": "log_message",
                    "message": (
                        "[INFO] execution lock released: "
                        f"task_id={task_id}, "
                        f"owner_type={owner.owner_type}, "
                        f"owner_id={owner.owner_id}"
                    ),
                },
            )

    def _run_single_cycle_step(
        self,
        *,
        repo_path: str,
        task_id: str,
        event_callback: RunTaskEventCallback | None = None,
    ) -> dict:
        self._emit(
            event_callback,
            {
                "type": "status_changed",
                "status": "running",
                "step": "show-next",
                "role": "",
                "cycle": "",
            },
        )
        show_next_result = ShowNextUseCase().execute(
            repo_path=repo_path,
            task_id=task_id,
        )
        self._emit(
            event_callback,
            {
                "type": "show_next_ready",
                "result": show_next_result,
            },
        )

        role = str(show_next_result["role"])
        cycle = int(show_next_result["cycle"])
        prompt_path = str(show_next_result["prompt_path"])
        output_json_path = str(show_next_result["output_json_path"])

        self._emit(
            event_callback,
            {
                "type": "status_changed",
                "status": "running",
                "step": "show-next",
                "role": role,
                "cycle": str(cycle),
            },
        )
        self._emit(
            event_callback,
            {
                "type": "monitor_message",
                "message": "show-next completed",
            },
        )
        self._emit(
            event_callback,
            {
                "type": "monitor_message",
                "message": f"role / cycle: {role} / {cycle}",
            },
        )
        self._emit(
            event_callback,
            {
                "type": "log_message",
                "message": (
                    "[INFO] show-next completed: "
                    f"task_id={task_id}, role={role}, cycle={cycle}"
                ),
            },
        )

        prompt_text = Path(prompt_path).read_text(encoding="utf-8")
        if not prompt_text.strip():
            raise ValueError("prompt text is empty.")

        self._emit(
            event_callback,
            {
                "type": "status_changed",
                "status": "running",
                "step": "claude",
                "role": role,
                "cycle": str(cycle),
            },
        )
        self._emit(
            event_callback,
            {
                "type": "monitor_message",
                "message": "process started",
            },
        )
        self._emit(
            event_callback,
            {
                "type": "monitor_message",
                "message": f"cwd: {Path(repo_path).resolve()}",
            },
        )
        self._emit(
            event_callback,
            {
                "type": "log_message",
                "message": (
                    "[INFO] claude step started: "
                    f"task_id={task_id}, role={role}, cycle={cycle}"
                ),
            },
        )
        self._emit(
            event_callback,
            {
                "type": "log_message",
                "message": f"[INFO] claude cwd: {Path(repo_path).resolve()}",
            },
        )

        claude_result = run_claude_print_mode(
            repo_path=repo_path,
            prompt_text=prompt_text,
        )

        self._emit(
            event_callback,
            {
                "type": "log_message",
                "message": (
                    "[INFO] claude finished: "
                    f"returncode={claude_result.returncode}, "
                    f"command={' '.join(claude_result.command)}"
                ),
            },
        )

        stdout_text = claude_result.stdout.strip()
        stderr_text = claude_result.stderr.strip()

        if stdout_text:
            self._emit(event_callback, {"type": "monitor_message", "message": "stdout"})
            self._emit(event_callback, {"type": "monitor_message", "message": stdout_text})
            self._emit(event_callback, {"type": "log_message", "message": "[INFO] claude stdout:"})
            self._emit(event_callback, {"type": "log_message", "message": stdout_text})

        if stderr_text:
            self._emit(event_callback, {"type": "monitor_message", "message": "stderr"})
            self._emit(event_callback, {"type": "monitor_message", "message": stderr_text})
            self._emit(event_callback, {"type": "log_message", "message": "[INFO] claude stderr:"})
            self._emit(event_callback, {"type": "log_message", "message": stderr_text})

        if claude_result.returncode != 0:
            raise RuntimeError(
                "claude command failed. "
                f"returncode={claude_result.returncode}"
            )

        if not Path(output_json_path).exists():
            raise FileNotFoundError(f"Report file not found: {output_json_path}")

        self._emit(
            event_callback,
            {
                "type": "monitor_message",
                "message": "report file detected",
            },
        )
        self._emit(
            event_callback,
            {
                "type": "log_message",
                "message": f"[INFO] report json saved: {output_json_path}",
            },
        )

        self._emit(
            event_callback,
            {
                "type": "status_changed",
                "status": "running",
                "step": "validate-report",
                "role": role,
                "cycle": str(cycle),
            },
        )
        validate_result = ValidateReportUseCase().execute(
            repo_path=repo_path,
            task_id=task_id,
            role=role,
            expected_cycle=cycle,
        )
        validation_text = (
            f"valid: {validate_result['valid']}\n"
            f"role: {validate_result['role']}\n"
            f"cycle: {validate_result['cycle']}\n"
            f"report_path: {validate_result['report_path']}"
        )
        self._emit(
            event_callback,
            {
                "type": "validation_ready",
                "text": validation_text,
            },
        )
        self._emit(
            event_callback,
            {
                "type": "monitor_message",
                "message": "validate success",
            },
        )
        self._emit(
            event_callback,
            {
                "type": "log_message",
                "message": (
                    "[INFO] validate-report success: "
                    f"task_id={task_id}, "
                    f"role={validate_result['role']}, "
                    f"cycle={validate_result['cycle']}"
                ),
            },
        )

        self._emit(
            event_callback,
            {
                "type": "status_changed",
                "status": "running",
                "step": "advance",
                "role": role,
                "cycle": str(cycle),
            },
        )
        advance_result = AdvanceTaskUseCase().execute(
            repo_path=repo_path,
            task_id=task_id,
            expected_role=role,
            expected_cycle=cycle,
        )
        self._emit(
            event_callback,
            {
                "type": "monitor_message",
                "message": (
                    "advanced to next role: "
                    f"{advance_result['next_role']} "
                    f"(status={advance_result['status']}, "
                    f"cycle={advance_result['cycle']})"
                ),
            },
        )
        self._emit(
            event_callback,
            {
                "type": "log_message",
                "message": (
                    "[INFO] advance completed: "
                    f"task_id={task_id}, "
                    f"status={advance_result['status']}, "
                    f"current={advance_result['current_stage']}, "
                    f"next={advance_result['next_role']}, "
                    f"cycle={advance_result['cycle']}"
                ),
            },
        )
        self._emit(
            event_callback,
            {
                "type": "task_detail_requested",
                "task_id": task_id,
            },
        )
        self._emit(
            event_callback,
            {
                "type": "task_list_refresh_requested",
            },
        )

        return advance_result

    @staticmethod
    def _emit(
        event_callback: RunTaskEventCallback | None,
        payload: dict,
    ) -> None:
        if event_callback is not None:
            event_callback(payload)
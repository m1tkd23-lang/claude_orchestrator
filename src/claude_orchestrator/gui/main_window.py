# src\claude_orchestrator\gui\main_window.py
from __future__ import annotations

from PySide6.QtCore import QThread, QTimer
from PySide6.QtWidgets import QMainWindow

from claude_orchestrator.gui.main_window_actions import MainWindowActionsMixin
from claude_orchestrator.gui.main_window_auto_run import MainWindowAutoRunMixin
from claude_orchestrator.gui.main_window_planner import MainWindowPlannerMixin
from claude_orchestrator.gui.main_window_remote import MainWindowRemoteMixin
from claude_orchestrator.gui.main_window_view_state import MainWindowViewStateMixin
from claude_orchestrator.gui.state_helpers import apply_initial_state
from claude_orchestrator.gui.ui_sections import (
    build_main_window_ui,
    connect_main_window_signals,
)


class MainWindow(
    MainWindowActionsMixin,
    MainWindowAutoRunMixin,
    MainWindowPlannerMixin,
    MainWindowRemoteMixin,
    MainWindowViewStateMixin,
    QMainWindow,
):
    def __init__(self) -> None:
        super().__init__()

        self.setWindowTitle("Claude Orchestrator GUI MVP")
        self.resize(1600, 950)

        self._last_prompt_path: str = ""
        self._last_output_json_path: str = ""
        self._current_task_id: str = ""
        self._selected_task_id: str = ""
        self._active_pipeline_task_id: str = ""
        self._follow_active_pipeline_task: bool = True
        self._last_repo_path: str = ""

        self._auto_run_thread: QThread | None = None
        self._auto_run_worker = None
        self._auto_run_active: bool = False
        self._last_auto_run_completion_status: str = ""
        self._pending_auto_planner_after_completion: bool = False
        self._stop_after_current_task_requested: bool = False

        self._planner_thread: QThread | None = None
        self._planner_worker = None
        self._planner_active: bool = False
        self._pending_auto_plan_director_after_planner: bool = False

        self._planner_report: dict | None = None
        self._planner_state_store = None
        self._planner_selected_proposal_id: str = ""
        self._planner_role: str = "planner_safe"
        self._development_mode: str = "maintenance"

        self._plan_director_thread: QThread | None = None
        self._plan_director_worker = None
        self._plan_director_active: bool = False
        self._plan_director_report: dict | None = None
        self._pending_auto_approve_next_task: bool = False

        self._waiting_next_task_approval: bool = False
        self._auto_approve_next_task: bool = False
        self._pipeline_auto_approval_warning_expanded: bool = False

        self._remote_sync_timer: QTimer | None = None
        self._remote_sync_interval_ms: int = 30_000
        self._remote_sync_in_progress: bool = False

        self._default_reference_doc_paths = [
            r"README.md",
            r".claude_orchestrator\docs\task_history\過去TASK作業記録.md",
            r".claude_orchestrator\docs\task_maps\TASKフロー全体図.md",
        ]

        build_main_window_ui(self)
        connect_main_window_signals(self)
        apply_initial_state(self)

        self._reset_execution_view()
        self._reset_planner_view()
        self._reset_remote_view()
        self._clear_pipeline_tab()
        self._refresh_pipeline_controls()
        self._refresh_pipeline_tab()
        self._start_remote_sync_timer()

    def closeEvent(self, event) -> None:  # type: ignore[override]
        self._stop_remote_sync_timer()

        if self._auto_run_thread is not None and self._auto_run_thread.isRunning():
            self._auto_run_thread.quit()
            self._auto_run_thread.wait(1000)

        if self._planner_thread is not None and self._planner_thread.isRunning():
            self._planner_thread.quit()
            self._planner_thread.wait(1000)

        if (
            self._plan_director_thread is not None
            and self._plan_director_thread.isRunning()
        ):
            self._plan_director_thread.quit()
            self._plan_director_thread.wait(1000)

        super().closeEvent(event)
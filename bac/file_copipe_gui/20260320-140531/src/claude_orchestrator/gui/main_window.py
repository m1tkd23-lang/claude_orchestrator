# src\claude_orchestrator\gui\main_window.py
from __future__ import annotations

from PySide6.QtCore import QThread
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

        self._plan_director_thread: QThread | None = None
        self._plan_director_worker = None
        self._plan_director_active: bool = False
        self._plan_director_report: dict | None = None

        self._waiting_next_task_approval: bool = False

        self._default_reference_doc_paths = [
            r"docs\Claude Orchestrator GUI 開発記録 & 次工程指示書.md",
            r"docs\workflow_rules.md",
            r"docs\planner_v1_仕様書.md",
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

    def closeEvent(self, event) -> None:  # type: ignore[override]
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
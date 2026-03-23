# src\claude_orchestrator\gui\ui_sections.py
from __future__ import annotations

from typing import Any

from PySide6.QtWidgets import QTabWidget, QVBoxLayout, QWidget

from claude_orchestrator.gui.tabs.detail_tab import build_detail_tab
from claude_orchestrator.gui.tabs.execution_tab import build_execution_tab
from claude_orchestrator.gui.tabs.remote_tab import build_remote_tab


def build_main_window_ui(window: Any) -> None:
    central = QWidget()
    window.setCentralWidget(central)

    root_layout = QVBoxLayout(central)
    root_layout.setContentsMargins(8, 8, 8, 8)
    root_layout.setSpacing(8)

    window.main_tabs = QTabWidget()
    root_layout.addWidget(window.main_tabs)

    window.main_tabs.addTab(build_execution_tab(window), "実行")
    window.main_tabs.addTab(build_remote_tab(window), "Remote Claude")
    window.main_tabs.addTab(build_detail_tab(window), "詳細")


def connect_main_window_signals(window: Any) -> None:
    window.btn_repo_browse.clicked.connect(window.on_browse_repo)
    window.btn_check_init.clicked.connect(window.on_check_initialized)
    window.btn_init_project.clicked.connect(window.on_init_project)
    window.btn_create_task.clicked.connect(window.on_create_task)
    window.btn_refresh_tasks.clicked.connect(window.on_refresh_tasks)
    window.task_list_widget.itemSelectionChanged.connect(window.on_task_selected)

    window.btn_run_claude_step.clicked.connect(window.on_run_claude_step)

    window.btn_connect_remote_claude.clicked.connect(window.on_connect_remote_claude)
    window.btn_reload_remote_state.clicked.connect(window.on_reload_remote_state)
    window.btn_copy_remote_url.clicked.connect(window.on_copy_remote_url)

    window.btn_start_remote_operator.clicked.connect(
        window.on_copy_remote_operator_prompt
    )

    window.btn_show_next.clicked.connect(window.on_show_next)
    window.btn_validate.clicked.connect(window.on_validate_report)
    window.btn_advance.clicked.connect(window.on_advance_task)
    window.btn_reload_selected.clicked.connect(window.on_reload_selected_task)

    window.btn_generate_next_tasks.clicked.connect(window.on_generate_next_tasks)
    window.planner_proposal_list_widget.itemSelectionChanged.connect(
        window.on_planner_proposal_selected
    )
    window.btn_accept_proposal.clicked.connect(window.on_accept_proposal)
    window.btn_create_task_from_proposal.clicked.connect(
        window.on_create_task_from_proposal
    )
    window.btn_reject_proposal.clicked.connect(window.on_reject_proposal)
    window.btn_defer_proposal.clicked.connect(window.on_defer_proposal)

    window.repo_path_edit.editingFinished.connect(window.on_repo_path_edited)
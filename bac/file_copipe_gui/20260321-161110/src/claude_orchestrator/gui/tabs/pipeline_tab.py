# src\claude_orchestrator\gui\tabs\pipeline_tab.py
from __future__ import annotations

from typing import Any

from PySide6.QtWidgets import (
    QGridLayout,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPlainTextEdit,
    QPushButton,
    QRadioButton,
    QVBoxLayout,
    QWidget,
)


def build_pipeline_tab(window: Any) -> QWidget:
    tab = QWidget()
    layout = QVBoxLayout(tab)
    layout.setContentsMargins(0, 0, 0, 0)
    layout.setSpacing(8)

    layout.addWidget(_build_pipeline_task_summary_group(window))
    layout.addWidget(_build_pipeline_role_state_group(window))
    layout.addWidget(_build_pipeline_report_summary_group(window), stretch=1)

    return tab


def _build_pipeline_task_summary_group(window: Any) -> QGroupBox:
    group = QGroupBox("pipeline task サマリ")
    layout = QGridLayout(group)

    window.pipeline_task_id_edit = _create_readonly_line_edit()
    window.pipeline_title_edit = _create_readonly_line_edit()
    window.pipeline_status_edit = _create_readonly_line_edit()
    window.pipeline_current_stage_edit = _create_readonly_line_edit()
    window.pipeline_next_role_edit = _create_readonly_line_edit()
    window.pipeline_cycle_edit = _create_readonly_line_edit()
    window.pipeline_last_completed_role_edit = _create_readonly_line_edit()
    window.pipeline_planner_role_edit = _create_readonly_line_edit()
    window.pipeline_post_flow_status_edit = _create_readonly_line_edit()
    window.pipeline_stop_reservation_edit = _create_readonly_line_edit()

    layout.addWidget(QLabel("task_id"), 0, 0)
    layout.addWidget(window.pipeline_task_id_edit, 0, 1)
    layout.addWidget(QLabel("title"), 1, 0)
    layout.addWidget(window.pipeline_title_edit, 1, 1)
    layout.addWidget(QLabel("status"), 2, 0)
    layout.addWidget(window.pipeline_status_edit, 2, 1)
    layout.addWidget(QLabel("current_stage"), 3, 0)
    layout.addWidget(window.pipeline_current_stage_edit, 3, 1)
    layout.addWidget(QLabel("next_role"), 4, 0)
    layout.addWidget(window.pipeline_next_role_edit, 4, 1)

    layout.addWidget(QLabel("cycle"), 0, 2)
    layout.addWidget(window.pipeline_cycle_edit, 0, 3)
    layout.addWidget(QLabel("last_completed_role"), 1, 2)
    layout.addWidget(window.pipeline_last_completed_role_edit, 1, 3)
    layout.addWidget(QLabel("planner_role"), 2, 2)
    layout.addWidget(window.pipeline_planner_role_edit, 2, 3)
    layout.addWidget(QLabel("後工程状態"), 3, 2)
    layout.addWidget(window.pipeline_post_flow_status_edit, 3, 3)
    layout.addWidget(QLabel("停止予約"), 4, 2)
    layout.addWidget(window.pipeline_stop_reservation_edit, 4, 3)

    approval_group = QGroupBox("承認モード")
    approval_layout = QVBoxLayout(approval_group)

    radio_row = QHBoxLayout()
    window.pipeline_manual_approval_radio = QRadioButton("手動承認")
    window.pipeline_auto_approval_radio = QRadioButton("自動承認")
    window.pipeline_manual_approval_radio.setChecked(True)

    radio_row.addWidget(window.pipeline_manual_approval_radio)
    radio_row.addWidget(window.pipeline_auto_approval_radio)
    radio_row.addStretch()

    toggle_row = QHBoxLayout()
    window.pipeline_auto_approval_warning_toggle_btn = QPushButton("警告を表示")
    toggle_row.addWidget(window.pipeline_auto_approval_warning_toggle_btn)
    toggle_row.addStretch()

    window.pipeline_auto_approval_warning_edit = QPlainTextEdit()
    window.pipeline_auto_approval_warning_edit.setReadOnly(True)
    window.pipeline_auto_approval_warning_edit.setFixedHeight(56)
    window.pipeline_auto_approval_warning_edit.setVisible(False)

    approval_layout.addLayout(radio_row)
    approval_layout.addLayout(toggle_row)
    approval_layout.addWidget(window.pipeline_auto_approval_warning_edit)

    layout.addWidget(approval_group, 5, 0, 1, 4)

    return group


def _build_pipeline_role_state_group(window: Any) -> QGroupBox:
    group = QGroupBox("pipeline role 状態")
    layout = QHBoxLayout(group)

    for role in [
        "task_router",
        "implementer",
        "reviewer",
        "director",
        "planner",
        "plan_director",
    ]:
        layout.addWidget(_build_role_state_card(window, role))

    return group


def _build_role_state_card(window: Any, role: str) -> QGroupBox:
    group = QGroupBox(role)
    layout = QGridLayout(group)

    state_edit = _create_readonly_line_edit()
    note_edit = _create_readonly_line_edit()

    setattr(window, f"pipeline_role_{role}_state_edit", state_edit)
    setattr(window, f"pipeline_role_{role}_note_edit", note_edit)

    layout.addWidget(QLabel("state"), 0, 0)
    layout.addWidget(state_edit, 0, 1)
    layout.addWidget(QLabel("note"), 1, 0)
    layout.addWidget(note_edit, 1, 1)
    return group


def _build_pipeline_report_summary_group(window: Any) -> QGroupBox:
    group = QGroupBox("role report 要約")
    layout = QGridLayout(group)

    layout.addWidget(_build_report_card(window, "task_router", "task_router"), 0, 0)
    layout.addWidget(_build_report_card(window, "implementer", "implementer"), 0, 1)
    layout.addWidget(_build_report_card(window, "reviewer", "reviewer"), 1, 0)
    layout.addWidget(_build_report_card(window, "director", "director"), 1, 1)
    layout.addWidget(_build_report_card(window, "planner", "planner"), 2, 0)
    layout.addWidget(
        _build_report_card(window, "plan_director", "plan_director"),
        2,
        1,
    )
    return group


def _build_report_card(window: Any, key: str, title: str) -> QGroupBox:
    group = QGroupBox(title)
    layout = QVBoxLayout(group)

    edit = QPlainTextEdit()
    edit.setReadOnly(True)
    edit.setFixedHeight(150)

    setattr(window, f"pipeline_{key}_summary_edit", edit)
    layout.addWidget(edit)
    return group


def _create_readonly_line_edit() -> QLineEdit:
    widget = QLineEdit()
    widget.setReadOnly(True)
    return widget
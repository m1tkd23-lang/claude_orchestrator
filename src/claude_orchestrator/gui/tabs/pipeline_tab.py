# src\claude_orchestrator\gui\tabs\pipeline_tab.py
from __future__ import annotations

from typing import Any

from PySide6.QtWidgets import (
    QComboBox,
    QGridLayout,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPlainTextEdit,
    QPushButton,
    QRadioButton,
    QSizePolicy,
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
    root_layout = QVBoxLayout(group)
    root_layout.setContentsMargins(8, 8, 8, 8)
    root_layout.setSpacing(6)

    header_layout = QGridLayout()
    header_layout.setHorizontalSpacing(8)
    header_layout.setVerticalSpacing(6)

    window.pipeline_task_id_edit = _create_readonly_line_edit()
    window.pipeline_title_edit = _create_readonly_line_edit()

    header_layout.addWidget(QLabel("task_id"), 0, 0)
    header_layout.addWidget(window.pipeline_task_id_edit, 0, 1)
    header_layout.addWidget(QLabel("title"), 0, 2)
    header_layout.addWidget(window.pipeline_title_edit, 0, 3)

    header_layout.setColumnStretch(1, 1)
    header_layout.setColumnStretch(3, 3)

    root_layout.addLayout(header_layout)

    toggle_row = QHBoxLayout()
    window.pipeline_task_summary_toggle_btn = QPushButton("詳細を表示")
    toggle_row.addWidget(window.pipeline_task_summary_toggle_btn)
    toggle_row.addStretch()
    root_layout.addLayout(toggle_row)

    window.pipeline_task_summary_detail_container = QWidget()
    detail_layout = QVBoxLayout(window.pipeline_task_summary_detail_container)
    detail_layout.setContentsMargins(0, 0, 0, 0)
    detail_layout.setSpacing(6)

    fields_grid = QGridLayout()
    fields_grid.setHorizontalSpacing(8)
    fields_grid.setVerticalSpacing(6)

    window.pipeline_status_edit = _create_readonly_line_edit()
    window.pipeline_current_stage_edit = _create_readonly_line_edit()
    window.pipeline_next_role_edit = _create_readonly_line_edit()
    window.pipeline_cycle_edit = _create_readonly_line_edit()
    window.pipeline_last_completed_role_edit = _create_readonly_line_edit()
    window.pipeline_planner_role_edit = _create_readonly_line_edit()
    window.pipeline_post_flow_status_edit = _create_readonly_line_edit()
    window.pipeline_stop_reservation_edit = _create_readonly_line_edit()
    window.pipeline_development_mode_combo = QComboBox()
    window.pipeline_development_mode_combo.addItem("mainline", "mainline")
    window.pipeline_development_mode_combo.addItem("maintenance", "maintenance")

    fields_grid.addWidget(QLabel("status"), 0, 0)
    fields_grid.addWidget(window.pipeline_status_edit, 0, 1)
    fields_grid.addWidget(QLabel("cycle"), 0, 2)
    fields_grid.addWidget(window.pipeline_cycle_edit, 0, 3)

    fields_grid.addWidget(QLabel("current_stage"), 1, 0)
    fields_grid.addWidget(window.pipeline_current_stage_edit, 1, 1)
    fields_grid.addWidget(QLabel("last_completed_role"), 1, 2)
    fields_grid.addWidget(window.pipeline_last_completed_role_edit, 1, 3)

    fields_grid.addWidget(QLabel("next_role"), 2, 0)
    fields_grid.addWidget(window.pipeline_next_role_edit, 2, 1)
    fields_grid.addWidget(QLabel("planner_role"), 2, 2)
    fields_grid.addWidget(window.pipeline_planner_role_edit, 2, 3)

    fields_grid.addWidget(QLabel("後工程状態"), 3, 0)
    fields_grid.addWidget(window.pipeline_post_flow_status_edit, 3, 1)
    fields_grid.addWidget(QLabel("停止予約"), 3, 2)
    fields_grid.addWidget(window.pipeline_stop_reservation_edit, 3, 3)

    fields_grid.addWidget(QLabel("development_mode"), 4, 0)
    fields_grid.addWidget(window.pipeline_development_mode_combo, 4, 1)
    fields_grid.addWidget(QWidget(), 4, 2)
    fields_grid.addWidget(QWidget(), 4, 3)

    fields_grid.setColumnStretch(1, 1)
    fields_grid.setColumnStretch(3, 1)

    detail_layout.addLayout(fields_grid)
    detail_layout.addWidget(_build_pipeline_approval_group(window))

    window.pipeline_task_summary_detail_container.setVisible(False)
    root_layout.addWidget(window.pipeline_task_summary_detail_container)

    return group


def _build_pipeline_approval_group(window: Any) -> QGroupBox:
    approval_group = QGroupBox("承認モード")
    approval_layout = QVBoxLayout(approval_group)
    approval_layout.setContentsMargins(8, 8, 8, 8)
    approval_layout.setSpacing(6)

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

    return approval_group


def _build_pipeline_role_state_group(window: Any) -> QGroupBox:
    group = QGroupBox("pipeline role 状態")
    layout = QHBoxLayout(group)
    layout.setContentsMargins(8, 8, 8, 8)
    layout.setSpacing(8)

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
    group.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Preferred)

    layout = QGridLayout(group)
    layout.setHorizontalSpacing(6)
    layout.setVerticalSpacing(6)

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
    layout.setContentsMargins(8, 8, 8, 8)
    layout.setHorizontalSpacing(8)
    layout.setVerticalSpacing(8)

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

    for row in range(3):
        layout.setRowStretch(row, 1)
    for col in range(2):
        layout.setColumnStretch(col, 1)

    return group


def _build_report_card(window: Any, key: str, title: str) -> QGroupBox:
    group = QGroupBox(title)
    group.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)

    layout = QVBoxLayout(group)
    layout.setContentsMargins(6, 6, 6, 6)

    edit = QPlainTextEdit()
    edit.setReadOnly(True)
    edit.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)

    setattr(window, f"pipeline_{key}_summary_edit", edit)
    layout.addWidget(edit)
    return group


def _create_readonly_line_edit() -> QLineEdit:
    widget = QLineEdit()
    widget.setReadOnly(True)
    return widget
# src\claude_orchestrator\gui\tabs\detail_tab.py
from __future__ import annotations

from typing import Any

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QGridLayout,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QListWidget,
    QPlainTextEdit,
    QPushButton,
    QSplitter,
    QVBoxLayout,
    QWidget,
)


def build_detail_tab(window: Any) -> QWidget:
    tab = QWidget()
    layout = QVBoxLayout(tab)
    layout.setContentsMargins(0, 0, 0, 0)
    layout.setSpacing(8)

    vertical_splitter = QSplitter(Qt.Vertical)
    layout.addWidget(vertical_splitter)

    top_splitter = QSplitter(Qt.Horizontal)
    top_splitter.addWidget(_build_left_top_panel(window))
    top_splitter.addWidget(_build_right_top_panel(window))
    top_splitter.setStretchFactor(0, 2)
    top_splitter.setStretchFactor(1, 3)

    bottom_widget = QWidget()
    bottom_layout = QVBoxLayout(bottom_widget)
    bottom_layout.setContentsMargins(0, 0, 0, 0)
    bottom_layout.setSpacing(8)
    bottom_layout.addWidget(_build_prompt_group(window), stretch=3)
    bottom_layout.addWidget(_build_output_path_group(window))
    bottom_layout.addWidget(_build_validation_group(window))

    vertical_splitter.addWidget(top_splitter)
    vertical_splitter.addWidget(bottom_widget)
    vertical_splitter.setStretchFactor(0, 3)
    vertical_splitter.setStretchFactor(1, 2)

    return tab


def _build_left_top_panel(window: Any) -> QWidget:
    widget = QWidget()
    layout = QVBoxLayout(widget)
    layout.setContentsMargins(0, 0, 0, 0)
    layout.setSpacing(8)
    layout.addWidget(_build_task_detail_group(window))
    layout.addWidget(_build_manual_action_group(window))
    return widget


def _build_right_top_panel(window: Any) -> QWidget:
    widget = QWidget()
    layout = QVBoxLayout(widget)
    layout.setContentsMargins(0, 0, 0, 0)
    layout.setSpacing(8)
    layout.addWidget(_build_planner_group(window))
    return widget


def _build_task_detail_group(window: Any) -> QGroupBox:
    group = QGroupBox("task 詳細")
    layout = QGridLayout(group)

    window.detail_task_id = QLineEdit()
    window.detail_title = QLineEdit()
    window.detail_description = QPlainTextEdit()
    window.detail_status = QLineEdit()
    window.detail_current_stage = QLineEdit()
    window.detail_next_role = QLineEdit()
    window.detail_cycle = QLineEdit()
    window.detail_last_completed_role = QLineEdit()
    window.detail_max_cycles = QLineEdit()
    window.detail_task_dir = QLineEdit()

    for widget in [
        window.detail_task_id,
        window.detail_title,
        window.detail_status,
        window.detail_current_stage,
        window.detail_next_role,
        window.detail_cycle,
        window.detail_last_completed_role,
        window.detail_max_cycles,
        window.detail_task_dir,
    ]:
        widget.setReadOnly(True)

    window.detail_description.setReadOnly(True)
    window.detail_description.setFixedHeight(120)

    layout.addWidget(QLabel("task_id"), 0, 0)
    layout.addWidget(window.detail_task_id, 0, 1)
    layout.addWidget(QLabel("title"), 1, 0)
    layout.addWidget(window.detail_title, 1, 1)
    layout.addWidget(QLabel("description"), 2, 0)
    layout.addWidget(window.detail_description, 2, 1)
    layout.addWidget(QLabel("status"), 3, 0)
    layout.addWidget(window.detail_status, 3, 1)
    layout.addWidget(QLabel("current_stage"), 4, 0)
    layout.addWidget(window.detail_current_stage, 4, 1)
    layout.addWidget(QLabel("next_role"), 5, 0)
    layout.addWidget(window.detail_next_role, 5, 1)
    layout.addWidget(QLabel("cycle"), 6, 0)
    layout.addWidget(window.detail_cycle, 6, 1)
    layout.addWidget(QLabel("last_completed_role"), 7, 0)
    layout.addWidget(window.detail_last_completed_role, 7, 1)
    layout.addWidget(QLabel("max_cycles"), 8, 0)
    layout.addWidget(window.detail_max_cycles, 8, 1)
    layout.addWidget(QLabel("task_dir"), 9, 0)
    layout.addWidget(window.detail_task_dir, 9, 1)
    return group


def _build_manual_action_group(window: Any) -> QGroupBox:
    group = QGroupBox("手動操作")
    layout = QVBoxLayout(group)

    status_row = QGridLayout()
    window.current_prompt_path_edit = QLineEdit()
    window.current_prompt_path_edit.setReadOnly(True)

    window.current_output_json_path_edit = QLineEdit()
    window.current_output_json_path_edit.setReadOnly(True)

    status_row.addWidget(QLabel("prompt path"), 0, 0)
    status_row.addWidget(window.current_prompt_path_edit, 0, 1)
    status_row.addWidget(QLabel("output json path"), 1, 0)
    status_row.addWidget(window.current_output_json_path_edit, 1, 1)

    button_row = QHBoxLayout()
    window.btn_show_next = QPushButton("show-next")
    window.btn_validate = QPushButton("validate-report")
    window.btn_advance = QPushButton("advance")
    window.btn_reload_selected = QPushButton("再読込")

    button_row.addWidget(window.btn_show_next)
    button_row.addWidget(window.btn_validate)
    button_row.addWidget(window.btn_advance)
    button_row.addWidget(window.btn_reload_selected)
    button_row.addStretch()

    layout.addLayout(status_row)
    layout.addLayout(button_row)
    return group


def _build_planner_group(window: Any) -> QGroupBox:
    group = QGroupBox("次タスク案")
    layout = QVBoxLayout(group)

    top_row = QHBoxLayout()
    window.btn_generate_next_tasks = QPushButton("次タスク案作成")
    top_row.addWidget(window.btn_generate_next_tasks)
    top_row.addStretch()

    splitter = QSplitter(Qt.Horizontal)

    left_widget = QWidget()
    left_layout = QVBoxLayout(left_widget)
    left_layout.setContentsMargins(0, 0, 0, 0)
    left_layout.setSpacing(6)

    window.planner_summary_edit = QPlainTextEdit()
    window.planner_summary_edit.setReadOnly(True)
    window.planner_summary_edit.setFixedHeight(100)

    window.planner_proposal_list_widget = QListWidget()

    left_layout.addWidget(QLabel("planner summary"))
    left_layout.addWidget(window.planner_summary_edit)
    left_layout.addWidget(QLabel("proposal list"))
    left_layout.addWidget(window.planner_proposal_list_widget)

    right_widget = QWidget()
    right_layout = QVBoxLayout(right_widget)
    right_layout.setContentsMargins(0, 0, 0, 0)
    right_layout.setSpacing(6)

    window.planner_proposal_detail_edit = QPlainTextEdit()
    window.planner_proposal_detail_edit.setReadOnly(True)

    action_row = QHBoxLayout()
    window.btn_accept_proposal = QPushButton("採用して task 作成欄へ転記")
    window.btn_create_task_from_proposal = QPushButton("task を直接作成")
    window.btn_reject_proposal = QPushButton("否決")
    window.btn_defer_proposal = QPushButton("保留")

    action_row.addWidget(window.btn_accept_proposal)
    action_row.addWidget(window.btn_create_task_from_proposal)
    action_row.addWidget(window.btn_reject_proposal)
    action_row.addWidget(window.btn_defer_proposal)
    action_row.addStretch()

    right_layout.addWidget(QLabel("proposal detail"))
    right_layout.addWidget(window.planner_proposal_detail_edit)
    right_layout.addLayout(action_row)

    splitter.addWidget(left_widget)
    splitter.addWidget(right_widget)
    splitter.setStretchFactor(0, 2)
    splitter.setStretchFactor(1, 3)

    layout.addLayout(top_row)
    layout.addWidget(splitter)
    return group


def _build_prompt_group(window: Any) -> QGroupBox:
    group = QGroupBox("prompt 表示")
    layout = QVBoxLayout(group)

    window.prompt_text_edit = QPlainTextEdit()
    window.prompt_text_edit.setReadOnly(True)

    layout.addWidget(window.prompt_text_edit)
    return group


def _build_output_path_group(window: Any) -> QGroupBox:
    group = QGroupBox("output json path")
    layout = QVBoxLayout(group)

    window.output_path_detail_edit = QPlainTextEdit()
    window.output_path_detail_edit.setReadOnly(True)
    window.output_path_detail_edit.setFixedHeight(90)

    layout.addWidget(window.output_path_detail_edit)
    return group


def _build_validation_group(window: Any) -> QGroupBox:
    group = QGroupBox("validation 結果")
    layout = QVBoxLayout(group)

    window.validation_result_edit = QPlainTextEdit()
    window.validation_result_edit.setReadOnly(True)
    window.validation_result_edit.setFixedHeight(120)

    layout.addWidget(window.validation_result_edit)
    return group
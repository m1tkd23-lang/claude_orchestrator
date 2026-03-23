# src\claude_orchestrator\gui\tabs\execution_tab.py
from __future__ import annotations

from typing import Any

from PySide6.QtWidgets import (
    QGridLayout,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QListWidget,
    QPlainTextEdit,
    QPushButton,
    QSizePolicy,
    QVBoxLayout,
    QWidget,
)


def build_execution_tab(window: Any) -> QWidget:
    tab = QWidget()
    layout = QHBoxLayout(tab)
    layout.setContentsMargins(0, 0, 0, 0)
    layout.setSpacing(8)

    left_widget = QWidget()
    left_layout = QVBoxLayout(left_widget)
    left_layout.setContentsMargins(0, 0, 0, 0)
    left_layout.setSpacing(8)
    left_layout.addWidget(_build_repo_group(window))
    left_layout.addWidget(_build_task_create_group(window))
    left_layout.addWidget(_build_task_list_group(window), stretch=1)

    right_widget = QWidget()
    right_layout = QVBoxLayout(right_widget)
    right_layout.setContentsMargins(0, 0, 0, 0)
    right_layout.setSpacing(8)
    right_layout.addWidget(_build_current_status_group(window))
    right_layout.addWidget(_build_execution_action_group(window))
    right_layout.addWidget(_build_execution_state_group(window))
    right_layout.addWidget(_build_claude_monitor_group(window), stretch=2)
    right_layout.addWidget(_build_log_group(window), stretch=2)

    layout.addWidget(left_widget, 2)
    layout.addWidget(right_widget, 3)
    return tab


def _build_repo_group(window: Any) -> QGroupBox:
    group = QGroupBox("対象 repo")
    layout = QGridLayout(group)

    window.repo_path_edit = QLineEdit()
    window.repo_path_edit.setPlaceholderText(r"D:\Develop\repos\your_target_repo")

    window.btn_repo_browse = QPushButton("参照")
    window.btn_check_init = QPushButton("初期化確認")
    window.btn_init_project = QPushButton("init-project")

    layout.addWidget(QLabel("repo path"), 0, 0)
    layout.addWidget(window.repo_path_edit, 0, 1, 1, 3)
    layout.addWidget(window.btn_repo_browse, 0, 4)
    layout.addWidget(window.btn_check_init, 1, 3)
    layout.addWidget(window.btn_init_project, 1, 4)
    return group


def _build_task_create_group(window: Any) -> QGroupBox:
    group = QGroupBox("新規 task 作成")
    layout = QGridLayout(group)

    window.task_title_edit = QLineEdit()
    window.task_desc_edit = QPlainTextEdit()
    window.task_desc_edit.setPlaceholderText("task description")
    window.task_desc_edit.setFixedHeight(90)

    window.context_files_edit = QPlainTextEdit()
    window.context_files_edit.setPlaceholderText("1行1ファイル")
    window.context_files_edit.setFixedHeight(80)

    window.constraints_edit = QPlainTextEdit()
    window.constraints_edit.setPlaceholderText("1行1制約")
    window.constraints_edit.setFixedHeight(80)

    window.btn_create_task = QPushButton("task作成")

    layout.addWidget(QLabel("title"), 0, 0)
    layout.addWidget(window.task_title_edit, 0, 1)
    layout.addWidget(QLabel("description"), 1, 0)
    layout.addWidget(window.task_desc_edit, 1, 1)
    layout.addWidget(QLabel("context files"), 2, 0)
    layout.addWidget(window.context_files_edit, 2, 1)
    layout.addWidget(QLabel("constraints"), 3, 0)
    layout.addWidget(window.constraints_edit, 3, 1)
    layout.addWidget(window.btn_create_task, 4, 1)
    return group


def _build_task_list_group(window: Any) -> QGroupBox:
    group = QGroupBox("task 一覧")
    layout = QVBoxLayout(group)

    top_row = QHBoxLayout()
    window.btn_refresh_tasks = QPushButton("一覧更新")
    top_row.addStretch()
    top_row.addWidget(window.btn_refresh_tasks)

    window.task_list_widget = QListWidget()
    window.task_list_widget.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)

    layout.addLayout(top_row)
    layout.addWidget(window.task_list_widget)
    return group


def _build_current_status_group(window: Any) -> QGroupBox:
    group = QGroupBox("選択 task の現在ステータス")
    layout = QGridLayout(group)

    window.current_task_id_edit = QLineEdit()
    window.current_task_title_edit = QLineEdit()
    window.current_task_status_edit = QLineEdit()
    window.current_task_next_role_edit = QLineEdit()
    window.current_task_cycle_edit = QLineEdit()

    for widget in [
        window.current_task_id_edit,
        window.current_task_title_edit,
        window.current_task_status_edit,
        window.current_task_next_role_edit,
        window.current_task_cycle_edit,
    ]:
        widget.setReadOnly(True)

    layout.addWidget(QLabel("task_id"), 0, 0)
    layout.addWidget(window.current_task_id_edit, 0, 1)
    layout.addWidget(QLabel("title"), 1, 0)
    layout.addWidget(window.current_task_title_edit, 1, 1)
    layout.addWidget(QLabel("status"), 2, 0)
    layout.addWidget(window.current_task_status_edit, 2, 1)
    layout.addWidget(QLabel("next_role"), 3, 0)
    layout.addWidget(window.current_task_next_role_edit, 3, 1)
    layout.addWidget(QLabel("cycle"), 4, 0)
    layout.addWidget(window.current_task_cycle_edit, 4, 1)
    return group


def _build_execution_action_group(window: Any) -> QGroupBox:
    group = QGroupBox("Claude実行")
    layout = QVBoxLayout(group)

    button_row = QHBoxLayout()
    window.btn_run_claude_step = QPushButton("Claude実行(自動完了まで)")
    window.btn_request_stop_after_current_task = QPushButton("完了後停止予約")
    button_row.addWidget(window.btn_run_claude_step)
    button_row.addWidget(window.btn_request_stop_after_current_task)
    button_row.addStretch()

    layout.addLayout(button_row)
    return group


def _build_execution_state_group(window: Any) -> QGroupBox:
    group = QGroupBox("実行状態表示")
    layout = QGridLayout(group)

    window.execution_status_edit = QLineEdit()
    window.execution_status_edit.setReadOnly(True)
    window.execution_step_edit = QLineEdit()
    window.execution_step_edit.setReadOnly(True)
    window.execution_role_edit = QLineEdit()
    window.execution_role_edit.setReadOnly(True)
    window.execution_cycle_edit = QLineEdit()
    window.execution_cycle_edit.setReadOnly(True)

    layout.addWidget(QLabel("実行状態"), 0, 0)
    layout.addWidget(window.execution_status_edit, 0, 1)
    layout.addWidget(QLabel("現在ステップ"), 1, 0)
    layout.addWidget(window.execution_step_edit, 1, 1)
    layout.addWidget(QLabel("現在ロール"), 2, 0)
    layout.addWidget(window.execution_role_edit, 2, 1)
    layout.addWidget(QLabel("現在サイクル"), 3, 0)
    layout.addWidget(window.execution_cycle_edit, 3, 1)
    return group


def _build_claude_monitor_group(window: Any) -> QGroupBox:
    group = QGroupBox("Claude実行モニタ")
    layout = QVBoxLayout(group)

    window.claude_monitor_edit = QPlainTextEdit()
    window.claude_monitor_edit.setReadOnly(True)

    layout.addWidget(window.claude_monitor_edit)
    return group


def _build_log_group(window: Any) -> QGroupBox:
    group = QGroupBox("結果ログ")
    layout = QVBoxLayout(group)

    window.log_edit = QPlainTextEdit()
    window.log_edit.setReadOnly(True)

    layout.addWidget(window.log_edit)
    return group
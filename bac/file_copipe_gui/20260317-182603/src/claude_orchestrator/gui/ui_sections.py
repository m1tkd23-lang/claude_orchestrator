# src\claude_orchestrator\gui\ui_sections.py
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
    QPushButton,
    QPlainTextEdit,
    QSizePolicy,
    QSplitter,
    QVBoxLayout,
    QWidget,
)


def build_main_window_ui(window: Any) -> None:
    central = QWidget()
    window.setCentralWidget(central)

    root_layout = QVBoxLayout(central)
    root_layout.setContentsMargins(8, 8, 8, 8)
    root_layout.setSpacing(8)

    splitter = QSplitter(Qt.Horizontal)
    root_layout.addWidget(splitter)

    left_widget = QWidget()
    left_layout = QVBoxLayout(left_widget)
    left_layout.setContentsMargins(0, 0, 0, 0)
    left_layout.setSpacing(8)

    left_layout.addWidget(build_repo_group(window))
    left_layout.addWidget(build_task_create_group(window))
    left_layout.addWidget(build_task_list_group(window), stretch=1)

    center_widget = QWidget()
    center_layout = QVBoxLayout(center_widget)
    center_layout.setContentsMargins(0, 0, 0, 0)
    center_layout.setSpacing(8)

    center_layout.addWidget(build_task_detail_group(window))
    center_layout.addWidget(build_action_group(window))
    center_layout.addWidget(build_log_group(window), stretch=1)

    right_widget = QWidget()
    right_layout = QVBoxLayout(right_widget)
    right_layout.setContentsMargins(0, 0, 0, 0)
    right_layout.setSpacing(8)

    right_layout.addWidget(build_prompt_group(window), stretch=3)
    right_layout.addWidget(build_output_path_group(window))
    right_layout.addWidget(build_validation_group(window))

    splitter.addWidget(left_widget)
    splitter.addWidget(center_widget)
    splitter.addWidget(right_widget)
    splitter.setStretchFactor(0, 2)
    splitter.setStretchFactor(1, 3)
    splitter.setStretchFactor(2, 4)


def connect_main_window_signals(window: Any) -> None:
    window.btn_repo_browse.clicked.connect(window.on_browse_repo)
    window.btn_check_init.clicked.connect(window.on_check_initialized)
    window.btn_init_project.clicked.connect(window.on_init_project)
    window.btn_create_task.clicked.connect(window.on_create_task)
    window.btn_refresh_tasks.clicked.connect(window.on_refresh_tasks)
    window.task_list_widget.itemSelectionChanged.connect(window.on_task_selected)
    window.btn_show_next.clicked.connect(window.on_show_next)
    window.btn_validate.clicked.connect(window.on_validate_report)
    window.btn_advance.clicked.connect(window.on_advance_task)
    window.btn_reload_selected.clicked.connect(window.on_reload_selected_task)
    window.repo_path_edit.editingFinished.connect(window.on_repo_path_edited)


def build_repo_group(window: Any) -> QGroupBox:
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


def build_task_create_group(window: Any) -> QGroupBox:
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


def build_task_list_group(window: Any) -> QGroupBox:
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


def build_task_detail_group(window: Any) -> QGroupBox:
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

    read_only_line_edits = [
        window.detail_task_id,
        window.detail_title,
        window.detail_status,
        window.detail_current_stage,
        window.detail_next_role,
        window.detail_cycle,
        window.detail_last_completed_role,
        window.detail_max_cycles,
        window.detail_task_dir,
    ]
    for widget in read_only_line_edits:
        widget.setReadOnly(True)

    window.detail_description.setReadOnly(True)
    window.detail_description.setFixedHeight(100)

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


def build_action_group(window: Any) -> QGroupBox:
    group = QGroupBox("操作")
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


def build_prompt_group(window: Any) -> QGroupBox:
    group = QGroupBox("prompt 表示")
    layout = QVBoxLayout(group)

    window.prompt_text_edit = QPlainTextEdit()
    window.prompt_text_edit.setReadOnly(True)

    layout.addWidget(window.prompt_text_edit)
    return group


def build_output_path_group(window: Any) -> QGroupBox:
    group = QGroupBox("次に保存すべき JSON パス")
    layout = QVBoxLayout(group)

    window.output_path_detail_edit = QPlainTextEdit()
    window.output_path_detail_edit.setReadOnly(True)
    window.output_path_detail_edit.setFixedHeight(70)

    layout.addWidget(window.output_path_detail_edit)
    return group


def build_validation_group(window: Any) -> QGroupBox:
    group = QGroupBox("validation 結果")
    layout = QVBoxLayout(group)

    window.validation_result_edit = QPlainTextEdit()
    window.validation_result_edit.setReadOnly(True)
    window.validation_result_edit.setFixedHeight(90)

    layout.addWidget(window.validation_result_edit)
    return group


def build_log_group(window: Any) -> QGroupBox:
    group = QGroupBox("ログ")
    layout = QVBoxLayout(group)

    window.log_edit = QPlainTextEdit()
    window.log_edit.setReadOnly(True)

    layout.addWidget(window.log_edit)
    return group
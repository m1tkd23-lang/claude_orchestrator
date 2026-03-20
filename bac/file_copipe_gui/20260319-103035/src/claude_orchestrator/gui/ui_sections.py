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
    QTabWidget,
    QVBoxLayout,
    QWidget,
)


def build_main_window_ui(window: Any) -> None:
    central = QWidget()
    window.setCentralWidget(central)

    root_layout = QVBoxLayout(central)
    root_layout.setContentsMargins(8, 8, 8, 8)
    root_layout.setSpacing(8)

    window.main_tabs = QTabWidget()
    root_layout.addWidget(window.main_tabs)

    execution_tab = build_execution_tab(window)
    detail_tab = build_detail_tab(window)

    window.main_tabs.addTab(execution_tab, "実行")
    window.main_tabs.addTab(detail_tab, "詳細")


def build_execution_tab(window: Any) -> QWidget:
    tab = QWidget()
    layout = QHBoxLayout(tab)
    layout.setContentsMargins(0, 0, 0, 0)
    layout.setSpacing(8)

    splitter = QSplitter(Qt.Horizontal)
    layout.addWidget(splitter)

    left_widget = QWidget()
    left_layout = QVBoxLayout(left_widget)
    left_layout.setContentsMargins(0, 0, 0, 0)
    left_layout.setSpacing(8)

    left_layout.addWidget(build_repo_group(window))
    left_layout.addWidget(build_task_create_group(window))
    left_layout.addWidget(build_task_list_group(window), stretch=1)

    right_widget = QWidget()
    right_layout = QVBoxLayout(right_widget)
    right_layout.setContentsMargins(0, 0, 0, 0)
    right_layout.setSpacing(8)

    right_layout.addWidget(build_current_status_group(window))
    right_layout.addWidget(build_execution_action_group(window))
    right_layout.addWidget(build_execution_state_group(window))
    right_layout.addWidget(build_claude_monitor_group(window), stretch=2)
    right_layout.addWidget(build_log_group(window), stretch=2)

    splitter.addWidget(left_widget)
    splitter.addWidget(right_widget)
    splitter.setStretchFactor(0, 2)
    splitter.setStretchFactor(1, 3)

    return tab


def build_detail_tab(window: Any) -> QWidget:
    tab = QWidget()
    layout = QVBoxLayout(tab)
    layout.setContentsMargins(0, 0, 0, 0)
    layout.setSpacing(8)

    vertical_splitter = QSplitter(Qt.Vertical)
    layout.addWidget(vertical_splitter)

    top_splitter = QSplitter(Qt.Horizontal)

    left_widget = QWidget()
    left_layout = QVBoxLayout(left_widget)
    left_layout.setContentsMargins(0, 0, 0, 0)
    left_layout.setSpacing(8)
    left_layout.addWidget(build_task_detail_group(window))
    left_layout.addWidget(build_manual_action_group(window))

    right_widget = QWidget()
    right_layout = QVBoxLayout(right_widget)
    right_layout.setContentsMargins(0, 0, 0, 0)
    right_layout.setSpacing(8)
    right_layout.addWidget(build_planner_group(window))

    top_splitter.addWidget(left_widget)
    top_splitter.addWidget(right_widget)
    top_splitter.setStretchFactor(0, 2)
    top_splitter.setStretchFactor(1, 3)

    bottom_widget = QWidget()
    bottom_layout = QVBoxLayout(bottom_widget)
    bottom_layout.setContentsMargins(0, 0, 0, 0)
    bottom_layout.setSpacing(8)
    bottom_layout.addWidget(build_prompt_group(window), stretch=3)
    bottom_layout.addWidget(build_output_path_group(window))
    bottom_layout.addWidget(build_validation_group(window))

    vertical_splitter.addWidget(top_splitter)
    vertical_splitter.addWidget(bottom_widget)
    vertical_splitter.setStretchFactor(0, 3)
    vertical_splitter.setStretchFactor(1, 2)

    return tab


def connect_main_window_signals(window: Any) -> None:
    window.btn_repo_browse.clicked.connect(window.on_browse_repo)
    window.btn_check_init.clicked.connect(window.on_check_initialized)
    window.btn_init_project.clicked.connect(window.on_init_project)
    window.btn_create_task.clicked.connect(window.on_create_task)
    window.btn_refresh_tasks.clicked.connect(window.on_refresh_tasks)
    window.task_list_widget.itemSelectionChanged.connect(window.on_task_selected)
    window.btn_show_next.clicked.connect(window.on_show_next)
    window.btn_run_claude_step.clicked.connect(window.on_run_claude_step)
    window.btn_validate.clicked.connect(window.on_validate_report)
    window.btn_advance.clicked.connect(window.on_advance_task)
    window.btn_reload_selected.clicked.connect(window.on_reload_selected_task)

    window.btn_generate_next_tasks.clicked.connect(window.on_generate_next_tasks)
    window.planner_proposal_list_widget.itemSelectionChanged.connect(
        window.on_planner_proposal_selected
    )
    window.btn_accept_proposal.clicked.connect(window.on_accept_proposal)
    window.btn_reject_proposal.clicked.connect(window.on_reject_proposal)
    window.btn_defer_proposal.clicked.connect(window.on_defer_proposal)

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


def build_current_status_group(window: Any) -> QGroupBox:
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


def build_execution_action_group(window: Any) -> QGroupBox:
    group = QGroupBox("Claude実行")
    layout = QVBoxLayout(group)

    button_row = QHBoxLayout()
    window.btn_run_claude_step = QPushButton("Claude実行(自動完了まで)")
    button_row.addWidget(window.btn_run_claude_step)
    button_row.addStretch()

    layout.addLayout(button_row)

    return group


def build_execution_state_group(window: Any) -> QGroupBox:
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


def build_claude_monitor_group(window: Any) -> QGroupBox:
    group = QGroupBox("Claude実行モニタ")
    layout = QVBoxLayout(group)

    window.claude_monitor_edit = QPlainTextEdit()
    window.claude_monitor_edit.setReadOnly(True)

    layout.addWidget(window.claude_monitor_edit)
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


def build_manual_action_group(window: Any) -> QGroupBox:
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


def build_planner_group(window: Any) -> QGroupBox:
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
    window.btn_reject_proposal = QPushButton("否決")
    window.btn_defer_proposal = QPushButton("保留")

    action_row.addWidget(window.btn_accept_proposal)
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


def build_prompt_group(window: Any) -> QGroupBox:
    group = QGroupBox("prompt 表示")
    layout = QVBoxLayout(group)

    window.prompt_text_edit = QPlainTextEdit()
    window.prompt_text_edit.setReadOnly(True)

    layout.addWidget(window.prompt_text_edit)
    return group


def build_output_path_group(window: Any) -> QGroupBox:
    group = QGroupBox("output json path")
    layout = QVBoxLayout(group)

    window.output_path_detail_edit = QPlainTextEdit()
    window.output_path_detail_edit.setReadOnly(True)
    window.output_path_detail_edit.setFixedHeight(90)

    layout.addWidget(window.output_path_detail_edit)
    return group


def build_validation_group(window: Any) -> QGroupBox:
    group = QGroupBox("validation 結果")
    layout = QVBoxLayout(group)

    window.validation_result_edit = QPlainTextEdit()
    window.validation_result_edit.setReadOnly(True)
    window.validation_result_edit.setFixedHeight(120)

    layout.addWidget(window.validation_result_edit)
    return group


def build_log_group(window: Any) -> QGroupBox:
    group = QGroupBox("結果ログ")
    layout = QVBoxLayout(group)

    window.log_edit = QPlainTextEdit()
    window.log_edit.setReadOnly(True)

    layout.addWidget(window.log_edit)
    return group
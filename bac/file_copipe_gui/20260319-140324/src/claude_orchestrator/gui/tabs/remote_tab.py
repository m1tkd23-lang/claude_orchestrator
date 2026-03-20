# src\claude_orchestrator\gui\tabs\remote_tab.py
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
    QVBoxLayout,
    QWidget,
)


def build_remote_tab(window: Any) -> QWidget:
    tab = QWidget()
    layout = QVBoxLayout(tab)
    layout.setContentsMargins(0, 0, 0, 0)
    layout.setSpacing(8)

    layout.addWidget(_build_remote_control_group(window))
    layout.addStretch()
    return tab


def _build_remote_control_group(window: Any) -> QGroupBox:
    group = QGroupBox("Remote Claude")
    layout = QGridLayout(group)

    window.remote_session_name_edit = QLineEdit()

    window.remote_spawn_mode_combo = QComboBox()
    window.remote_spawn_mode_combo.addItems(["same-dir", "worktree", "session"])

    window.remote_permission_mode_combo = QComboBox()
    window.remote_permission_mode_combo.addItems(
        ["default", "acceptEdits", "bypassPermissions", "dontAsk", "plan"]
    )

    window.remote_status_edit = QLineEdit()
    window.remote_mode_edit = QLineEdit()
    window.remote_last_started_at_edit = QLineEdit()
    window.remote_bridge_url_edit = QLineEdit()
    window.remote_console_log_path_edit = QLineEdit()
    window.remote_server_pid_edit = QLineEdit()
    window.remote_current_menu_edit = QLineEdit()
    window.remote_previous_menu_edit = QLineEdit()
    window.remote_selected_task_id_edit = QLineEdit()
    window.remote_selected_source_task_id_edit = QLineEdit()
    window.remote_selected_proposal_id_edit = QLineEdit()
    window.remote_last_message_edit = QPlainTextEdit()
    window.remote_last_message_edit.setFixedHeight(120)

    for widget in [
        window.remote_status_edit,
        window.remote_mode_edit,
        window.remote_last_started_at_edit,
        window.remote_bridge_url_edit,
        window.remote_console_log_path_edit,
        window.remote_server_pid_edit,
        window.remote_current_menu_edit,
        window.remote_previous_menu_edit,
        window.remote_selected_task_id_edit,
        window.remote_selected_source_task_id_edit,
        window.remote_selected_proposal_id_edit,
    ]:
        widget.setReadOnly(True)

    window.remote_last_message_edit.setReadOnly(True)

    window.btn_connect_remote_claude = QPushButton("Remote Claude 接続")
    window.btn_reload_remote_state = QPushButton("状態再読込")
    window.btn_copy_remote_url = QPushButton("URLコピー")

    button_row = QHBoxLayout()
    button_row.addWidget(window.btn_connect_remote_claude)
    button_row.addWidget(window.btn_reload_remote_state)
    button_row.addWidget(window.btn_copy_remote_url)
    button_row.addStretch()

    row = 0
    layout.addWidget(QLabel("session_name"), row, 0)
    layout.addWidget(window.remote_session_name_edit, row, 1)
    row += 1
    layout.addWidget(QLabel("spawn_mode"), row, 0)
    layout.addWidget(window.remote_spawn_mode_combo, row, 1)
    row += 1
    layout.addWidget(QLabel("permission_mode"), row, 0)
    layout.addWidget(window.remote_permission_mode_combo, row, 1)
    row += 1
    layout.addWidget(QLabel("status"), row, 0)
    layout.addWidget(window.remote_status_edit, row, 1)
    row += 1
    layout.addWidget(QLabel("mode"), row, 0)
    layout.addWidget(window.remote_mode_edit, row, 1)
    row += 1
    layout.addWidget(QLabel("last_started_at"), row, 0)
    layout.addWidget(window.remote_last_started_at_edit, row, 1)
    row += 1
    layout.addWidget(QLabel("bridge_url"), row, 0)
    layout.addWidget(window.remote_bridge_url_edit, row, 1)
    row += 1
    layout.addWidget(QLabel("console_log_path"), row, 0)
    layout.addWidget(window.remote_console_log_path_edit, row, 1)
    row += 1
    layout.addWidget(QLabel("server_pid"), row, 0)
    layout.addWidget(window.remote_server_pid_edit, row, 1)
    row += 1
    layout.addWidget(QLabel("current_menu"), row, 0)
    layout.addWidget(window.remote_current_menu_edit, row, 1)
    row += 1
    layout.addWidget(QLabel("previous_menu"), row, 0)
    layout.addWidget(window.remote_previous_menu_edit, row, 1)
    row += 1
    layout.addWidget(QLabel("selected_task_id"), row, 0)
    layout.addWidget(window.remote_selected_task_id_edit, row, 1)
    row += 1
    layout.addWidget(QLabel("selected_source_task_id"), row, 0)
    layout.addWidget(window.remote_selected_source_task_id_edit, row, 1)
    row += 1
    layout.addWidget(QLabel("selected_proposal_id"), row, 0)
    layout.addWidget(window.remote_selected_proposal_id_edit, row, 1)
    row += 1
    layout.addWidget(QLabel("last_message"), row, 0)
    layout.addWidget(window.remote_last_message_edit, row, 1)
    row += 1
    layout.addLayout(button_row, row, 0, 1, 2)

    return group
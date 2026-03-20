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

    layout.addWidget(_build_remote_connection_settings_group(window))
    layout.addWidget(_build_remote_connection_status_group(window))
    layout.addWidget(_build_remote_operator_state_group(window), stretch=1)

    return tab


def _build_remote_connection_settings_group(window: Any) -> QGroupBox:
    group = QGroupBox("接続設定")
    layout = QGridLayout(group)

    window.remote_session_name_edit = QLineEdit()

    window.remote_spawn_mode_combo = QComboBox()
    window.remote_spawn_mode_combo.addItems(["same-dir", "worktree", "session"])

    window.remote_permission_mode_combo = QComboBox()
    window.remote_permission_mode_combo.addItems(
        ["default", "acceptEdits", "bypassPermissions", "dontAsk", "plan"]
    )

    window.btn_connect_remote_claude = QPushButton("Remote Claude 接続")
    window.btn_reload_remote_state = QPushButton("状態再読込")
    window.btn_copy_remote_url = QPushButton("URLコピー")

    window.btn_start_remote_operator = QPushButton("プロンプトコピー")

    button_row = QHBoxLayout()
    button_row.addWidget(window.btn_connect_remote_claude)
    button_row.addWidget(window.btn_reload_remote_state)
    button_row.addWidget(window.btn_copy_remote_url)
    button_row.addWidget(window.btn_start_remote_operator)  # ★ここに追加
    button_row.addStretch()

    layout.addWidget(QLabel("session_name"), 0, 0)
    layout.addWidget(window.remote_session_name_edit, 0, 1)
    layout.addWidget(QLabel("spawn_mode"), 1, 0)
    layout.addWidget(window.remote_spawn_mode_combo, 1, 1)
    layout.addWidget(QLabel("permission_mode"), 2, 0)
    layout.addWidget(window.remote_permission_mode_combo, 2, 1)
    layout.addLayout(button_row, 3, 0, 1, 2)

    return group


def _build_remote_connection_status_group(window: Any) -> QGroupBox:
    group = QGroupBox("接続状態")
    layout = QGridLayout(group)

    window.remote_status_edit = QLineEdit()
    window.remote_mode_edit = QLineEdit()
    window.remote_last_started_at_edit = QLineEdit()
    window.remote_bridge_url_edit = QLineEdit()
    window.remote_console_log_path_edit = QLineEdit()
    window.remote_server_pid_edit = QLineEdit()

    for widget in [
        window.remote_status_edit,
        window.remote_mode_edit,
        window.remote_last_started_at_edit,
        window.remote_bridge_url_edit,
        window.remote_console_log_path_edit,
        window.remote_server_pid_edit,
    ]:
        widget.setReadOnly(True)

    layout.addWidget(QLabel("status"), 0, 0)
    layout.addWidget(window.remote_status_edit, 0, 1)
    layout.addWidget(QLabel("mode"), 1, 0)
    layout.addWidget(window.remote_mode_edit, 1, 1)
    layout.addWidget(QLabel("last_started_at"), 2, 0)
    layout.addWidget(window.remote_last_started_at_edit, 2, 1)
    layout.addWidget(QLabel("bridge_url"), 3, 0)
    layout.addWidget(window.remote_bridge_url_edit, 3, 1)
    layout.addWidget(QLabel("console_log_path"), 4, 0)
    layout.addWidget(window.remote_console_log_path_edit, 4, 1)
    layout.addWidget(QLabel("server_pid"), 5, 0)
    layout.addWidget(window.remote_server_pid_edit, 5, 1)

    return group


def _build_remote_operator_state_group(window: Any) -> QGroupBox:
    group = QGroupBox("Remote Operator 状態")
    layout = QGridLayout(group)

    window.remote_current_menu_edit = QLineEdit()
    window.remote_previous_menu_edit = QLineEdit()
    window.remote_selected_task_id_edit = QLineEdit()
    window.remote_selected_source_task_id_edit = QLineEdit()
    window.remote_selected_proposal_id_edit = QLineEdit()
    window.remote_last_message_edit = QPlainTextEdit()
    window.remote_last_message_edit.setFixedHeight(140)

    for widget in [
        window.remote_current_menu_edit,
        window.remote_previous_menu_edit,
        window.remote_selected_task_id_edit,
        window.remote_selected_source_task_id_edit,
        window.remote_selected_proposal_id_edit,
    ]:
        widget.setReadOnly(True)

    window.remote_last_message_edit.setReadOnly(True)

    layout.addWidget(QLabel("current_menu"), 0, 0)
    layout.addWidget(window.remote_current_menu_edit, 0, 1)
    layout.addWidget(QLabel("previous_menu"), 1, 0)
    layout.addWidget(window.remote_previous_menu_edit, 1, 1)
    layout.addWidget(QLabel("selected_task_id"), 2, 0)
    layout.addWidget(window.remote_selected_task_id_edit, 2, 1)
    layout.addWidget(QLabel("selected_source_task_id"), 3, 0)
    layout.addWidget(window.remote_selected_source_task_id_edit, 3, 1)
    layout.addWidget(QLabel("selected_proposal_id"), 4, 0)
    layout.addWidget(window.remote_selected_proposal_id_edit, 4, 1)
    layout.addWidget(QLabel("last_message"), 5, 0)
    layout.addWidget(window.remote_last_message_edit, 5, 1)

    return group
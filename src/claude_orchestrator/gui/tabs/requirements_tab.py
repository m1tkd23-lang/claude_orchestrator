# src\claude_orchestrator\gui\tabs\requirements_tab.py
from __future__ import annotations

from typing import Any

from PySide6.QtWidgets import (
    QFormLayout,
    QGroupBox,
    QHBoxLayout,
    QLineEdit,
    QPlainTextEdit,
    QPushButton,
    QSplitter,
    QVBoxLayout,
    QWidget,
)


def build_requirements_tab(window: Any) -> QWidget:
    tab = QWidget()
    root_layout = QVBoxLayout(tab)
    root_layout.setContentsMargins(0, 0, 0, 0)
    root_layout.setSpacing(8)

    top_group = QGroupBox("requirements 操作")
    top_layout = QVBoxLayout(top_group)

    path_form = QFormLayout()
    window.requirements_path_edit = QLineEdit()
    window.requirements_path_edit.setReadOnly(True)
    path_form.addRow("requirements.json", window.requirements_path_edit)

    window.requirements_schema_path_edit = QLineEdit()
    window.requirements_schema_path_edit.setReadOnly(True)
    path_form.addRow("requirements.schema.json", window.requirements_schema_path_edit)

    window.requirements_status_edit = QLineEdit()
    window.requirements_status_edit.setReadOnly(True)
    path_form.addRow("状態", window.requirements_status_edit)

    top_layout.addLayout(path_form)

    change_group = QGroupBox("保存メタ情報")
    change_layout = QFormLayout(change_group)

    window.requirements_change_summary_edit = QLineEdit()
    window.requirements_change_summary_edit.setPlaceholderText(
        "変更概要を入力（例: target_users を更新）"
    )
    change_layout.addRow("change_summary", window.requirements_change_summary_edit)

    window.requirements_change_details_edit = QPlainTextEdit()
    window.requirements_change_details_edit.setPlaceholderText(
        "変更詳細を1行ずつ入力"
    )
    window.requirements_change_details_edit.setMaximumHeight(90)
    change_layout.addRow("change_details", window.requirements_change_details_edit)

    top_layout.addWidget(change_group)

    button_row = QHBoxLayout()
    window.btn_load_requirements = QPushButton("読込")
    window.btn_validate_requirements = QPushButton("検証")
    window.btn_save_requirements = QPushButton("保存")
    window.btn_generate_requirements_docs = QPushButton("docs生成")
    window.btn_run_requirements_refinement_loop = QPushButton("要件を完成させる")
    window.btn_create_task_from_requirements = QPushButton("タスク生成")
    button_row.addWidget(window.btn_load_requirements)
    button_row.addWidget(window.btn_validate_requirements)
    button_row.addWidget(window.btn_save_requirements)
    button_row.addWidget(window.btn_generate_requirements_docs)
    button_row.addWidget(window.btn_run_requirements_refinement_loop)
    button_row.addWidget(window.btn_create_task_from_requirements)
    button_row.addStretch(1)
    top_layout.addLayout(button_row)

    root_layout.addWidget(top_group)

    ai_group = QGroupBox("Claude 要件支援")
    ai_layout = QVBoxLayout(ai_group)

    ai_button_row = QHBoxLayout()
    window.btn_requirements_claude_suggest = QPushButton("Claudeで要件整理")
    window.btn_requirements_apply_claude_json = QPushButton("AI提案をeditorへ反映")
    ai_button_row.addWidget(window.btn_requirements_claude_suggest)
    ai_button_row.addWidget(window.btn_requirements_apply_claude_json)
    ai_button_row.addStretch(1)
    ai_layout.addLayout(ai_button_row)

    ai_splitter = QSplitter()
    ai_layout.addWidget(ai_splitter)

    request_group = QGroupBox("Claudeへの依頼内容")
    request_layout = QVBoxLayout(request_group)
    window.requirements_ai_request_edit = QPlainTextEdit()
    window.requirements_ai_request_edit.setPlaceholderText(
        "例:\n"
        "- このアプリの target_users と main_roles を整理してください\n"
        "- MVP機能を初心者向けに具体化してください\n"
        "- 足りない要件は open_questions に残してください"
    )
    request_layout.addWidget(window.requirements_ai_request_edit)
    ai_splitter.addWidget(request_group)

    response_group = QGroupBox("Claude提案JSON")
    response_layout = QVBoxLayout(response_group)
    window.requirements_ai_response_edit = QPlainTextEdit()
    window.requirements_ai_response_edit.setReadOnly(False)
    window.requirements_ai_response_edit.setPlaceholderText(
        "Claude が返した requirements.json 全文がここに表示されます"
    )
    response_layout.addWidget(window.requirements_ai_response_edit)
    ai_splitter.addWidget(response_group)
    ai_splitter.setSizes([500, 700])

    root_layout.addWidget(ai_group)

    content_splitter = QSplitter()
    root_layout.addWidget(content_splitter, 1)

    left_panel = QWidget()
    left_layout = QVBoxLayout(left_panel)
    left_layout.setContentsMargins(0, 0, 0, 0)
    left_layout.setSpacing(8)

    requirements_group = QGroupBox("requirements.json")
    requirements_layout = QVBoxLayout(requirements_group)
    window.requirements_json_edit = QPlainTextEdit()
    window.requirements_json_edit.setPlaceholderText(
        "requirements.json の内容がここに表示されます"
    )
    requirements_layout.addWidget(window.requirements_json_edit)
    left_layout.addWidget(requirements_group, 1)

    right_panel = QWidget()
    right_layout = QVBoxLayout(right_panel)
    right_layout.setContentsMargins(0, 0, 0, 0)
    right_layout.setSpacing(8)

    validation_group = QGroupBox("検証結果")
    validation_layout = QVBoxLayout(validation_group)
    window.requirements_validation_result_edit = QPlainTextEdit()
    window.requirements_validation_result_edit.setReadOnly(True)
    validation_layout.addWidget(window.requirements_validation_result_edit)
    right_layout.addWidget(validation_group, 1)

    open_questions_group = QGroupBox("open_questions.json")
    open_questions_layout = QVBoxLayout(open_questions_group)
    window.requirements_open_questions_edit = QPlainTextEdit()
    window.requirements_open_questions_edit.setReadOnly(True)
    open_questions_layout.addWidget(window.requirements_open_questions_edit)
    right_layout.addWidget(open_questions_group, 1)

    change_log_group = QGroupBox("requirements_change_log.json")
    change_log_layout = QVBoxLayout(change_log_group)
    window.requirements_change_log_edit = QPlainTextEdit()
    window.requirements_change_log_edit.setReadOnly(True)
    change_log_layout.addWidget(window.requirements_change_log_edit)
    right_layout.addWidget(change_log_group, 1)

    content_splitter.addWidget(left_panel)
    content_splitter.addWidget(right_panel)
    content_splitter.setSizes([900, 700])

    return tab
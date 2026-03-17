# src\claude_orchestrator\gui\dialog_helpers.py
from __future__ import annotations

from typing import Any

from PySide6.QtGui import QTextCursor
from PySide6.QtWidgets import QMessageBox


def append_log(window: Any, message: str) -> None:
    window.log_edit.appendPlainText(message)
    cursor = window.log_edit.textCursor()
    cursor.movePosition(QTextCursor.End)
    window.log_edit.setTextCursor(cursor)


def show_error(window: Any, title: str, exc: Exception) -> None:
    message = f"{type(exc).__name__}: {exc}"
    append_log(window, f"[ERROR] {message}")
    QMessageBox.critical(window, title, message)


def show_info(window: Any, title: str, message: str) -> None:
    append_log(window, f"[INFO] {message}")
    QMessageBox.information(window, title, message)
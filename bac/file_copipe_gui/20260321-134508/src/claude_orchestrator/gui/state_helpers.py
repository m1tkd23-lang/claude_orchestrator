# src\claude_orchestrator\gui\state_helpers.py
from __future__ import annotations

from pathlib import Path
from typing import Any

from PySide6.QtCore import Qt
from PySide6.QtWidgets import QListWidgetItem

from claude_orchestrator.application.usecases.status_usecase import StatusUseCase
from claude_orchestrator.gui.dialog_helpers import append_log


def apply_initial_state(window: Any) -> None:
    reset_repo_context(window, clear_log=False)
    append_log(window, "GUI ready.")


def get_repo_path(window: Any) -> str:
    return window.repo_path_edit.text().strip()


def normalize_repo_path(repo_path: str) -> str:
    if not repo_path:
        return ""
    try:
        return str(Path(repo_path).resolve())
    except Exception:
        return repo_path.strip()


def require_repo_path(window: Any) -> str:
    repo_path = get_repo_path(window)
    if not repo_path:
        raise ValueError("repo path is empty.")
    return repo_path


def require_selected_task_id(window: Any) -> str:
    if not window._current_task_id:
        raise ValueError("task is not selected.")
    return window._current_task_id


def parse_multiline_list(text: str) -> list[str]:
    return [line.strip() for line in text.splitlines() if line.strip()]


def clear_task_detail(window: Any) -> None:
    window.detail_task_id.clear()
    window.detail_title.clear()
    window.detail_description.clear()
    window.detail_status.clear()
    window.detail_current_stage.clear()
    window.detail_next_role.clear()
    window.detail_cycle.clear()
    window.detail_last_completed_role.clear()
    window.detail_max_cycles.clear()
    window.detail_task_dir.clear()

    window.current_task_id_edit.clear()
    window.current_task_title_edit.clear()
    window.current_task_status_edit.clear()
    window.current_task_next_role_edit.clear()
    window.current_task_cycle_edit.clear()

    window._current_task_id = ""


def clear_prompt_area(window: Any) -> None:
    window.current_prompt_path_edit.clear()
    window.current_output_json_path_edit.clear()
    window.prompt_text_edit.clear()
    window.output_path_detail_edit.clear()
    window._last_prompt_path = ""
    window._last_output_json_path = ""


def clear_validation_area(window: Any) -> None:
    window.validation_result_edit.clear()


def clear_task_list(window: Any) -> None:
    window.task_list_widget.clear()


def clear_monitor_area(window: Any) -> None:
    if hasattr(window, "claude_monitor_edit"):
        window.claude_monitor_edit.clear()


def clear_planner_area(window: Any) -> None:
    if hasattr(window, "planner_summary_edit"):
        window.planner_summary_edit.clear()
    if hasattr(window, "planner_proposal_list_widget"):
        window.planner_proposal_list_widget.clear()
    if hasattr(window, "planner_proposal_detail_edit"):
        window.planner_proposal_detail_edit.clear()


def reset_repo_context(window: Any, clear_log: bool = False) -> None:
    clear_task_list(window)
    clear_task_detail(window)
    clear_prompt_area(window)
    clear_validation_area(window)
    clear_monitor_area(window)
    clear_planner_area(window)
    if clear_log:
        window.log_edit.clear()


def set_task_detail(window: Any, data: dict[str, Any]) -> None:
    task_id = str(data.get("task_id", ""))
    title = str(data.get("title", ""))
    status = str(data.get("status", ""))
    next_role = str(data.get("next_role", ""))
    cycle = str(data.get("cycle", ""))

    window.detail_task_id.setText(task_id)
    window.detail_title.setText(title)
    window.detail_description.setPlainText(str(data.get("description", "")))
    window.detail_status.setText(status)
    window.detail_current_stage.setText(str(data.get("current_stage", "")))
    window.detail_next_role.setText(next_role)
    window.detail_cycle.setText(cycle)
    window.detail_last_completed_role.setText(str(data.get("last_completed_role", "")))
    window.detail_max_cycles.setText(str(data.get("max_cycles", "")))
    window.detail_task_dir.setText(str(data.get("task_dir", "")))

    window.current_task_id_edit.setText(task_id)
    window.current_task_title_edit.setText(title)
    window.current_task_status_edit.setText(status)
    window.current_task_next_role_edit.setText(next_role)
    window.current_task_cycle_edit.setText(cycle)

    window._current_task_id = task_id


def read_text_file_if_exists(path_str: str) -> str:
    path = Path(path_str)
    if not path.exists():
        return ""
    return path.read_text(encoding="utf-8")


def handle_repo_changed(window: Any, repo_path: str) -> None:
    normalized = normalize_repo_path(repo_path)
    if normalized == window._last_repo_path:
        return

    old_repo = window._last_repo_path
    window._last_repo_path = normalized
    reset_repo_context(window, clear_log=False)

    if normalized:
        if old_repo:
            append_log(window, f"[INFO] repo changed: {old_repo} -> {normalized}")
        else:
            append_log(window, f"[INFO] repo selected: {normalized}")


def refresh_task_list(window: Any) -> None:
    repo_path = require_repo_path(window)
    results = StatusUseCase().list_tasks(repo_path=repo_path)

    selected_task_id = window._current_task_id
    found_selected = False

    window.task_list_widget.clear()

    for item in results:
        text = (
            f"{item['task_id']} | "
            f"status={item['status']} | "
            f"current={item['current_stage']} | "
            f"next={item['next_role']} | "
            f"cycle={item['cycle']} | "
            f"title={item['title']}"
        )
        widget_item = QListWidgetItem(text)
        widget_item.setData(Qt.UserRole, item["task_id"])
        window.task_list_widget.addItem(widget_item)

    if selected_task_id:
        for i in range(window.task_list_widget.count()):
            item = window.task_list_widget.item(i)
            if str(item.data(Qt.UserRole)) == selected_task_id:
                window.task_list_widget.setCurrentItem(item)
                found_selected = True
                break

    if selected_task_id and not found_selected:
        clear_task_detail(window)
        clear_prompt_area(window)
        clear_validation_area(window)
        clear_planner_area(window)

    if not results:
        clear_task_detail(window)
        clear_prompt_area(window)
        clear_validation_area(window)
        clear_planner_area(window)

    append_log(window, f"[INFO] task list refreshed. count={len(results)}")


def load_selected_task_detail(window: Any, task_id: str) -> None:
    repo_path = require_repo_path(window)
    data = StatusUseCase().get_task_status(repo_path=repo_path, task_id=task_id)
    set_task_detail(window, data)
    append_log(window, f"[INFO] task detail loaded: {task_id}")
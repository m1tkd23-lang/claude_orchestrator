# src\claude_orchestrator\gui\state_helpers.py
from __future__ import annotations

from pathlib import Path
import json

from PySide6.QtCore import Qt
from PySide6.QtWidgets import QListWidgetItem

from claude_orchestrator.application.usecases.status_usecase import StatusUseCase


def normalize_repo_path(repo_path: str) -> str:
    return str(Path(repo_path).resolve()) if str(repo_path).strip() else ""


def get_repo_path(window) -> str:
    return str(window.repo_path_edit.text()).strip()


def require_repo_path(window) -> str:
    repo_path = normalize_repo_path(get_repo_path(window))
    if not repo_path:
        raise ValueError("repo path を入力してください。")
    if not Path(repo_path).exists():
        raise FileNotFoundError(f"repo path not found: {repo_path}")
    return repo_path


def handle_repo_changed(window, repo_path: str) -> None:
    normalized = normalize_repo_path(repo_path)
    previous = str(getattr(window, "_last_repo_path", "")).strip()
    if previous == normalized:
        return

    window._last_repo_path = normalized
    window._current_task_id = ""
    window._selected_task_id = ""
    window._active_pipeline_task_id = ""
    refresh_task_list(window)
    if hasattr(window, "_on_repo_context_changed"):
        window._on_repo_context_changed(normalized)


def apply_initial_state(window) -> None:
    window.task_list_widget.clear()
    window.task_detail_edit.clear()
    window.monitor_edit.clear()
    window.log_edit.clear()
    window.prompt_text_edit.clear()
    window.output_path_detail_edit.clear()
    window.current_prompt_path_edit.clear()
    window.current_output_json_path_edit.clear()
    window._current_task_id = ""
    window._selected_task_id = ""
    window._active_pipeline_task_id = ""
    window._follow_active_pipeline_task = True


def refresh_task_list(window) -> None:
    repo_path = normalize_repo_path(get_repo_path(window))
    window.task_list_widget.clear()

    if not repo_path or not Path(repo_path).exists():
        return

    tasks = StatusUseCase().list_tasks(repo_path=repo_path)
    for task in tasks:
        task_id = str(task.get("task_id", "")).strip()
        status = str(task.get("status", "")).strip()
        cycle = str(task.get("cycle", "")).strip()
        title = str(task.get("title", "")).strip()
        item = QListWidgetItem(
            f"{task_id} | status={status} | cycle={cycle} | title={title}"
        )
        item.setData(Qt.UserRole, task_id)
        window.task_list_widget.addItem(item)

    target_task_id = get_display_target_task_id(window)
    if target_task_id:
        sync_task_list_selection(window, target_task_id)


def sync_task_list_selection(window, task_id: str) -> bool:
    normalized = str(task_id).strip()
    if not normalized:
        return False

    for index in range(window.task_list_widget.count()):
        item = window.task_list_widget.item(index)
        if item is None:
            continue
        item_task_id = str(item.data(Qt.UserRole) or "").strip()
        if item_task_id != normalized:
            continue
        window.task_list_widget.blockSignals(True)
        window.task_list_widget.setCurrentItem(item)
        window.task_list_widget.blockSignals(False)
        return True
    return False


def set_selected_task(window, task_id: str) -> None:
    normalized = str(task_id).strip()
    window._selected_task_id = normalized
    if normalized:
        window._current_task_id = normalized
        sync_task_list_selection(window, normalized)


def set_active_pipeline_task(window, task_id: str) -> None:
    normalized = str(task_id).strip()
    window._active_pipeline_task_id = normalized
    if not normalized:
        return
    if bool(getattr(window, "_follow_active_pipeline_task", True)):
        window._selected_task_id = normalized
        window._current_task_id = normalized
        sync_task_list_selection(window, normalized)


def clear_active_pipeline_task(window) -> None:
    window._active_pipeline_task_id = ""


def get_display_target_task_id(window) -> str:
    if bool(getattr(window, "_follow_active_pipeline_task", True)):
        active_task_id = str(getattr(window, "_active_pipeline_task_id", "")).strip()
        if active_task_id:
            return active_task_id

    selected_task_id = str(getattr(window, "_selected_task_id", "")).strip()
    if selected_task_id:
        return selected_task_id

    current_task_id = str(getattr(window, "_current_task_id", "")).strip()
    if current_task_id:
        return current_task_id

    return ""


def require_selected_task_id(window) -> str:
    task_id = get_display_target_task_id(window)
    if not task_id:
        raise ValueError("task を選択してください。")
    return task_id


def load_selected_task_detail(window, task_id: str) -> None:
    repo_path = require_repo_path(window)
    normalized_task_id = str(task_id).strip()
    if not normalized_task_id:
        raise ValueError("task_id is empty.")

    detail = StatusUseCase().get_task_status(
        repo_path=repo_path,
        task_id=normalized_task_id,
    )

    detail_text = "\n".join(
        [
            f"Task ID     : {detail.get('task_id', '')}",
            f"Title       : {detail.get('title', '')}",
            f"Status      : {detail.get('status', '')}",
            f"Current     : {detail.get('current_stage', '')}",
            f"Next Role   : {detail.get('next_role', '')}",
            f"Cycle       : {detail.get('cycle', '')}",
            f"Revision    : {detail.get('revision', '')}",
        ]
    )
    window.task_detail_edit.setPlainText(detail_text)

    if bool(getattr(window, "_follow_active_pipeline_task", True)):
        set_active_pipeline_task(window, normalized_task_id)
    else:
        set_selected_task(window, normalized_task_id)

    window._current_task_id = normalized_task_id

    if hasattr(window, "_refresh_pipeline_tab"):
        window._refresh_pipeline_tab()


def read_text_file_if_exists(path: str) -> str:
    target = Path(path)
    if not target.exists():
        return ""
    return target.read_text(encoding="utf-8")


def clear_planner_area(window) -> None:
    window.planner_summary_edit.clear()
    window.planner_proposal_list_widget.clear()
    window.planner_proposal_detail_edit.clear()


def load_json_if_exists(path: Path) -> dict:
    if not path.exists():
        return {}
    with path.open("r", encoding="utf-8") as file:
        return json.load(file)
    
def parse_multiline_list(text: str) -> list[str]:
    return [
        line.strip()
        for line in str(text).splitlines()
        if line.strip()
    ]
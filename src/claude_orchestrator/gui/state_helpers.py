# src\claude_orchestrator\gui\state_helpers.py
from __future__ import annotations

import json
from pathlib import Path

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

    if hasattr(window, "current_task_id_edit"):
        window.current_task_id_edit.clear()
    if hasattr(window, "current_task_title_edit"):
        window.current_task_title_edit.clear()
    if hasattr(window, "current_task_status_edit"):
        window.current_task_status_edit.clear()
    if hasattr(window, "current_task_next_role_edit"):
        window.current_task_next_role_edit.clear()
    if hasattr(window, "current_task_cycle_edit"):
        window.current_task_cycle_edit.clear()

    window.claude_monitor_edit.clear()
    window.log_edit.clear()
    window.prompt_text_edit.clear()
    window.output_path_detail_edit.clear()
    window.current_prompt_path_edit.clear()
    window.current_output_json_path_edit.clear()

    clear_planner_area(window)

    if hasattr(window, "validation_result_edit"):
        window.validation_result_edit.clear()

    if hasattr(window, "plan_director_decision_edit"):
        window.plan_director_decision_edit.clear()
    if hasattr(window, "plan_director_selected_proposal_edit"):
        window.plan_director_selected_proposal_edit.clear()
    if hasattr(window, "plan_director_reason_edit"):
        window.plan_director_reason_edit.clear()
    if hasattr(window, "plan_director_scores_edit"):
        window.plan_director_scores_edit.clear()

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


def is_pipeline_running_or_waiting(window) -> bool:
    return bool(
        getattr(window, "_auto_run_active", False)
        or getattr(window, "_planner_active", False)
        or getattr(window, "_plan_director_active", False)
        or getattr(window, "_waiting_next_task_approval", False)
        or getattr(window, "_pending_auto_planner_after_completion", False)
        or getattr(window, "_pending_auto_plan_director_after_planner", False)
    )


def find_oldest_incomplete_task_id(window) -> str:
    repo_path = normalize_repo_path(get_repo_path(window))
    if not repo_path or not Path(repo_path).exists():
        return ""

    tasks = StatusUseCase().list_tasks(repo_path=repo_path)
    incomplete_task_ids = [
        str(task.get("task_id", "")).strip()
        for task in tasks
        if str(task.get("status", "")).strip() != "completed"
        and str(task.get("task_id", "")).strip()
    ]
    if not incomplete_task_ids:
        return ""

    return sorted(incomplete_task_ids)[0]


def get_display_target_task_id(window) -> str:
    if is_pipeline_running_or_waiting(window):
        active_task_id = str(getattr(window, "_active_pipeline_task_id", "")).strip()
        if active_task_id:
            return active_task_id

    selected_task_id = str(getattr(window, "_selected_task_id", "")).strip()
    if selected_task_id:
        return selected_task_id

    current_task_id = str(getattr(window, "_current_task_id", "")).strip()
    if current_task_id:
        return current_task_id

    oldest_incomplete_task_id = find_oldest_incomplete_task_id(window)
    if oldest_incomplete_task_id:
        return oldest_incomplete_task_id

    return ""


def require_selected_task_id(window) -> str:
    selected_task_id = str(getattr(window, "_selected_task_id", "")).strip()
    if selected_task_id:
        return selected_task_id

    current_task_id = str(getattr(window, "_current_task_id", "")).strip()
    if current_task_id:
        return current_task_id

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

    task_id_text = str(detail.get("task_id", ""))
    title_text = str(detail.get("title", ""))
    description_text = str(detail.get("description", ""))
    status_text = str(detail.get("status", ""))
    current_stage_text = str(detail.get("current_stage", ""))
    next_role_text = str(detail.get("next_role", ""))
    cycle_text = str(detail.get("cycle", ""))
    last_completed_role_text = str(detail.get("last_completed_role", ""))
    max_cycles_text = str(detail.get("max_cycles", ""))
    task_dir_text = str(detail.get("task_dir", ""))

    window.detail_task_id.setText(task_id_text)
    window.detail_title.setText(title_text)
    window.detail_description.setPlainText(description_text)
    window.detail_status.setText(status_text)
    window.detail_current_stage.setText(current_stage_text)
    window.detail_next_role.setText(next_role_text)
    window.detail_cycle.setText(cycle_text)
    window.detail_last_completed_role.setText(last_completed_role_text)
    window.detail_max_cycles.setText(max_cycles_text)
    window.detail_task_dir.setText(task_dir_text)

    if hasattr(window, "current_task_id_edit"):
        window.current_task_id_edit.setText(task_id_text)
    if hasattr(window, "current_task_title_edit"):
        window.current_task_title_edit.setText(title_text)
    if hasattr(window, "current_task_status_edit"):
        window.current_task_status_edit.setText(status_text)
    if hasattr(window, "current_task_next_role_edit"):
        window.current_task_next_role_edit.setText(next_role_text)
    if hasattr(window, "current_task_cycle_edit"):
        window.current_task_cycle_edit.setText(cycle_text)

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
    return [line.strip() for line in str(text).splitlines() if line.strip()]
# src\claude_orchestrator\core\task_factory.py
from __future__ import annotations

from datetime import datetime
from pathlib import Path
import json


def build_task_json(
    task_id: str,
    title: str,
    description: str,
    target_repo: Path,
    context_files: list[str] | None = None,
    constraints: list[str] | None = None,
    initial_execution_notes: list[str] | None = None,
) -> dict:
    return {
        "_meta": {
            "relative_path": ".claude_orchestrator/tasks/{task_id}/task.json".format(
                task_id=task_id
            )
        },
        "task_id": task_id,
        "title": title,
        "description": description,
        "target_repo": str(target_repo),
        "created_at": datetime.now().isoformat(timespec="seconds"),
        "context_files": context_files or [],
        "constraints": constraints or [],
        "task_type": None,
        "risk_level": None,
        "role_skill_plan": {
            "task_router": ["route-task"],
            "implementer": [],
            "reviewer": [],
            "director": [],
        },
        "skill_selection_source": None,
        "skill_selection_reason": [],
        "initial_execution_notes": initial_execution_notes or [],
    }


def build_state_json(
    task_id: str,
    max_cycles: int,
) -> dict:
    return {
        "_meta": {
            "relative_path": ".claude_orchestrator/tasks/{task_id}/state.json".format(
                task_id=task_id
            )
        },
        "task_id": task_id,
        "cycle": 1,
        "revision": 1,
        "status": "in_progress",
        "current_stage": "task_router",
        "next_role": "task_router",
        "last_completed_role": None,
        "max_cycles": max_cycles,
    }


def write_json(path: Path, data: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
        f.write("\n")
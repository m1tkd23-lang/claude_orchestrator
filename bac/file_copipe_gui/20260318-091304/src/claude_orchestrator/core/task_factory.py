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
        "status": "in_progress",
        "current_stage": "implementer",
        "next_role": "implementer",
        "last_completed_role": None,
        "max_cycles": max_cycles,
    }


def write_json(path: Path, data: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
        f.write("\n")
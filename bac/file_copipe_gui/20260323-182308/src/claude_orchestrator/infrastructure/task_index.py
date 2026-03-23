# src\claude_orchestrator\infrastructure\task_index.py
from __future__ import annotations

from pathlib import Path
import json


class TaskIndex:
    def __init__(self, tasks_root: Path) -> None:
        self.tasks_root = tasks_root

    def list_task_statuses(self) -> list[dict]:
        self.tasks_root.mkdir(parents=True, exist_ok=True)

        items: list[dict] = []

        for task_dir in sorted(self.tasks_root.iterdir(), key=lambda p: p.name):
            if not task_dir.is_dir():
                continue

            task_json_path = task_dir / "task.json"
            state_json_path = task_dir / "state.json"

            if not task_json_path.exists() or not state_json_path.exists():
                continue

            task_json = self._load_json(task_json_path)
            state_json = self._load_json(state_json_path)

            items.append(
                {
                    "task_id": task_json.get("task_id", task_dir.name),
                    "title": task_json.get("title", ""),
                    "status": state_json.get("status", ""),
                    "current_stage": state_json.get("current_stage", ""),
                    "next_role": state_json.get("next_role", ""),
                    "cycle": state_json.get("cycle", ""),
                    "last_completed_role": state_json.get("last_completed_role", None),
                    "task_dir": str(task_dir),
                }
            )

        return items

    @staticmethod
    def _load_json(path: Path) -> dict:
        with path.open("r", encoding="utf-8") as f:
            return json.load(f)
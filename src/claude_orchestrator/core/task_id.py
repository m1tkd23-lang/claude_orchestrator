# src\claude_orchestrator\core\task_id.py
from __future__ import annotations

from pathlib import Path


def next_task_id(tasks_root: Path, prefix: str = "TASK") -> str:
    tasks_root.mkdir(parents=True, exist_ok=True)

    max_number = 0

    for child in tasks_root.iterdir():
        if not child.is_dir():
            continue

        name = child.name.strip()
        if not name.startswith(f"{prefix}-"):
            continue

        suffix = name.removeprefix(f"{prefix}-")
        if not suffix.isdigit():
            continue

        value = int(suffix)
        if value > max_number:
            max_number = value

    next_number = max_number + 1
    return f"{prefix}-{next_number:04d}"
# src\claude_orchestrator\infrastructure\project_paths.py
from __future__ import annotations

from pathlib import Path
import json


class ProjectPaths:
    def __init__(self, target_repo: Path) -> None:
        self.target_repo = target_repo.resolve()
        self.root = self.target_repo / ".claude_orchestrator"
        self.config_dir = self.root / "config"
        self.tasks_dir = self.root / "tasks"
        self.runtime_dir = self.root / "runtime"
        self.project_config_path = self.config_dir / "project_config.json"

    def ensure_initialized(self) -> None:
        if not self.root.exists():
            raise FileNotFoundError(
                f".claude_orchestrator not found. Run init-project first: {self.root}"
            )

        if not self.project_config_path.exists():
            raise FileNotFoundError(
                f"project_config.json not found: {self.project_config_path}"
            )

    def load_project_config(self) -> dict:
        self.ensure_initialized()
        with self.project_config_path.open("r", encoding="utf-8") as f:
            return json.load(f)
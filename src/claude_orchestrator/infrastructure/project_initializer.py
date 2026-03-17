# src\claude_orchestrator\infrastructure\project_initializer.py
from __future__ import annotations

import json
import shutil
from pathlib import Path

from claude_orchestrator.services.template_service import get_project_bundle_root


class ProjectInitializer:
    def __init__(self, target_repo: Path) -> None:
        self.target_repo = target_repo
        self.bundle_root = get_project_bundle_root()
        self.target_root = self.target_repo / ".claude_orchestrator"

    def initialize(self, force: bool = False) -> Path:
        self._validate_target_repo()
        self._validate_bundle_root()

        if self.target_root.exists():
            if not force:
                raise FileExistsError(
                    f"Target already initialized: {self.target_root}"
                )
            shutil.rmtree(self.target_root)

        shutil.copytree(self.bundle_root, self.target_root)

        self._patch_project_config()

        return self.target_root

    def _validate_target_repo(self) -> None:
        if not self.target_repo.exists():
            raise FileNotFoundError(f"Target repo not found: {self.target_repo}")

        if not self.target_repo.is_dir():
            raise NotADirectoryError(f"Target repo is not a directory: {self.target_repo}")

    def _validate_bundle_root(self) -> None:
        if not self.bundle_root.exists():
            raise FileNotFoundError(f"Project bundle not found: {self.bundle_root}")

    def _patch_project_config(self) -> None:
        config_path = self.target_root / "config" / "project_config.json"

        if not config_path.exists():
            raise FileNotFoundError(f"project_config.json not found: {config_path}")

        with config_path.open("r", encoding="utf-8") as f:
            data = json.load(f)

        data["project_name"] = self.target_repo.name

        with config_path.open("w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
            f.write("\n")
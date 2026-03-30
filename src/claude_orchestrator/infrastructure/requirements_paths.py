# src\claude_orchestrator\infrastructure\requirements_paths.py
from __future__ import annotations

from pathlib import Path

from claude_orchestrator.infrastructure.project_paths import ProjectPaths


class RequirementsPaths:
    """requirements 関連ファイルのパス解決を行う."""

    def __init__(self, target_repo: Path) -> None:
        self._project_paths = ProjectPaths(target_repo)

    @property
    def repo_root(self) -> Path:
        return self._project_paths.target_repo

    @property
    def orchestrator_root(self) -> Path:
        return self._project_paths.root

    @property
    def requirements_dir(self) -> Path:
        return self.orchestrator_root / "requirements"

    @property
    def requirements_json(self) -> Path:
        return self.requirements_dir / "requirements.json"

    @property
    def requirements_change_log_json(self) -> Path:
        return self.requirements_dir / "requirements_change_log.json"

    @property
    def open_questions_json(self) -> Path:
        return self.requirements_dir / "open_questions.json"

    @property
    def requirements_schema_json(self) -> Path:
        return self.orchestrator_root / "schemas" / "requirements.schema.json"

    @property
    def project_core_purpose_doc(self) -> Path:
        return self.orchestrator_root / "docs" / "project_core" / "開発の目的本筋.md"

    @property
    def completion_definition_doc(self) -> Path:
        return self.orchestrator_root / "docs" / "completion_definition.md"

    @property
    def feature_inventory_doc(self) -> Path:
        return self.orchestrator_root / "docs" / "feature_inventory.md"

    def ensure_directories(self) -> None:
        self.requirements_dir.mkdir(parents=True, exist_ok=True)
        self.project_core_purpose_doc.parent.mkdir(parents=True, exist_ok=True)
        self.completion_definition_doc.parent.mkdir(parents=True, exist_ok=True)
        self.feature_inventory_doc.parent.mkdir(parents=True, exist_ok=True)
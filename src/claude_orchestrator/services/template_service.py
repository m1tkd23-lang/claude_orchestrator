# src\claude_orchestrator\services\template_service.py
from __future__ import annotations

from pathlib import Path


def get_project_bundle_root() -> Path:
    return (
        Path(__file__).resolve().parent.parent
        / "template_assets"
        / "project_bundle"
        / ".claude_orchestrator"
    )
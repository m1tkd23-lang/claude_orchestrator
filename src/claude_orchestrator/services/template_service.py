# src\claude_orchestrator\services\template_service.py
from __future__ import annotations

import sys
from pathlib import Path


def _get_runtime_base_dir() -> Path:
    if getattr(sys, "frozen", False):
        meipass = getattr(sys, "_MEIPASS", None)
        if meipass:
            return Path(meipass)
        return Path(sys.executable).resolve().parent

    return Path(__file__).resolve().parent.parent


def get_project_bundle_root() -> Path:
    base_dir = _get_runtime_base_dir()
    bundle_root = (
        base_dir
        / "template_assets"
        / "project_bundle"
        / ".claude_orchestrator"
    )

    if not bundle_root.exists():
        raise FileNotFoundError(
            "Project bundle not found. "
            f"Expected: {bundle_root}"
        )

    return bundle_root
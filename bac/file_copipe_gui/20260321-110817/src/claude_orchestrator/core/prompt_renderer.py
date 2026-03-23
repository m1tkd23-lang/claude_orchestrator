# src\claude_orchestrator\core\prompt_renderer.py
from __future__ import annotations


def render_prompt(template: str, **kwargs: str) -> str:
    return template.format(**kwargs)
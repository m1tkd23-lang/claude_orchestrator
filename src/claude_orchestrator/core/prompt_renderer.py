# src\claude_orchestrator\core\prompt_renderer.py
from __future__ import annotations

import re
from typing import Any

_PLACEHOLDER_PATTERN = re.compile(r"\{([a-zA-Z_][a-zA-Z0-9_]*)\}")


def render_prompt(template: str, **kwargs: Any) -> str:
    """
    Prompt template 内の既知プレースホルダだけを安全に置換する。

    例:
    - "{task_id}" のように kwargs に存在するキーは値へ置換する
    - "{N}" のように kwargs に存在しないキーはそのまま残す
    - JSON 例や説明文に含まれる一般的な波括弧は、上記パターンに一致しない限り触らない

    この実装により、str.format() が説明用の {N} などを誤って解釈して
    KeyError を起こす問題を防ぐ。
    """

    def _replace(match: re.Match[str]) -> str:
        key = match.group(1)
        if key in kwargs:
            value = kwargs[key]
            return "" if value is None else str(value)
        return match.group(0)

    return _PLACEHOLDER_PATTERN.sub(_replace, template)
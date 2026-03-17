# src\claude_orchestrator\services\claude_service.py
from __future__ import annotations

import asyncio
from dataclasses import dataclass
from typing import Sequence

from claude_agent_sdk import ClaudeAgentOptions, query


@dataclass(slots=True)
class ClaudeRunResult:
    final_text: str
    raw_messages: list[str]


class ClaudeService:
    def __init__(self, setting_sources: Sequence[str] | None = None) -> None:
        self.setting_sources = list(setting_sources or [])

    async def run_prompt_async(
        self,
        prompt: str,
        allowed_tools: list[str],
        system_prompt: str | None = None,
    ) -> ClaudeRunResult:
        options = ClaudeAgentOptions(
            allowed_tools=allowed_tools,
            system_prompt=system_prompt,
            setting_sources=self.setting_sources,
        )

        raw_messages: list[str] = []
        final_text_parts: list[str] = []

        async for message in query(
            prompt=prompt,
            options=options,
        ):
            text = self._extract_text(message)
            if text:
                raw_messages.append(text)
                final_text_parts.append(text)

        final_text = "\n".join(part for part in final_text_parts if part.strip()).strip()

        return ClaudeRunResult(
            final_text=final_text,
            raw_messages=raw_messages,
        )

    def run_prompt(
        self,
        prompt: str,
        allowed_tools: list[str],
        system_prompt: str | None = None,
    ) -> ClaudeRunResult:
        return asyncio.run(
            self.run_prompt_async(
                prompt=prompt,
                allowed_tools=allowed_tools,
                system_prompt=system_prompt,
            )
        )

    @staticmethod
    def _extract_text(message: object) -> str:
        if message is None:
            return ""

        for attr_name in ("result", "content", "text"):
            value = getattr(message, attr_name, None)
            if isinstance(value, str) and value.strip():
                return value

        return str(message)
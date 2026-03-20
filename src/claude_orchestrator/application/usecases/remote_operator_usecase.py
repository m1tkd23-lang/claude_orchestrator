# src\claude_orchestrator\application\usecases\remote_operator_usecase.py
from __future__ import annotations

from claude_orchestrator.application.remote_operator.controller import (
    RemoteOperatorController,
)


class RemoteOperatorUseCase:
    def __init__(self) -> None:
        self._controller = RemoteOperatorController()

    def show_menu(self, *, repo_path: str) -> dict:
        return self._controller.show_menu(repo_path=repo_path)

    def handle_input(
        self,
        *,
        repo_path: str,
        user_input: str,
    ) -> dict:
        return self._controller.handle_input(
            repo_path=repo_path,
            user_input=user_input,
        )
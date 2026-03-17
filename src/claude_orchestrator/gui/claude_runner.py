# src\claude_orchestrator\gui\claude_runner.py
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import shutil
import subprocess


@dataclass
class ClaudeRunResult:
    returncode: int
    stdout: str
    stderr: str
    command: list[str]


def run_claude_print_mode(
    *,
    repo_path: str,
    prompt_text: str,
    timeout_seconds: int = 300,
) -> ClaudeRunResult:
    claude_path = shutil.which("claude.cmd") or shutil.which("claude")
    if not claude_path:
        raise FileNotFoundError(
            "claude command not found. "
            "Ensure Claude CLI is installed and available in PATH."
        )

    command = [
        str(Path(claude_path).resolve()),
        "-p",
        "--permission-mode",
        "bypassPermissions",
    ]

    completed = subprocess.run(
        command,
        input=prompt_text,
        text=True,
        capture_output=True,
        cwd=str(Path(repo_path).resolve()),
        timeout=timeout_seconds,
        encoding="utf-8",
        errors="replace",
        shell=False,
    )

    return ClaudeRunResult(
        returncode=completed.returncode,
        stdout=completed.stdout,
        stderr=completed.stderr,
        command=command,
    )
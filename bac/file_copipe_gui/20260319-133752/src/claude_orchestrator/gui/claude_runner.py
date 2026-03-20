# src\claude_orchestrator\gui\claude_runner.py
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import shutil
import subprocess
import sys


@dataclass
class ClaudeRunResult:
    returncode: int
    stdout: str
    stderr: str
    command: list[str]


@dataclass
class ClaudeRemoteStartResult:
    command: list[str]
    session_name: str
    pid: int | None


def _resolve_claude_path() -> Path:
    claude_path = shutil.which("claude.cmd") or shutil.which("claude")
    if not claude_path:
        raise FileNotFoundError(
            "claude command not found. "
            "Ensure Claude CLI is installed and available in PATH."
        )
    return Path(claude_path).resolve()


def run_claude_print_mode(
    *,
    repo_path: str,
    prompt_text: str,
    timeout_seconds: int = 300,
) -> ClaudeRunResult:
    claude_path = _resolve_claude_path()

    command = [
        str(claude_path),
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


def start_claude_remote_control_session(
    *,
    repo_path: str,
    session_name: str,
) -> ClaudeRemoteStartResult:
    claude_path = _resolve_claude_path()
    normalized_session_name = str(session_name).strip() or "orchestrator-remote"

    command = [
        str(claude_path),
        "remote-control",
        "--name",
        normalized_session_name,
    ]

    creationflags = 0
    popen_kwargs: dict = {}
    if sys.platform.startswith("win"):
        creationflags = subprocess.CREATE_NEW_PROCESS_GROUP | subprocess.DETACHED_PROCESS

    process = subprocess.Popen(
        command,
        cwd=str(Path(repo_path).resolve()),
        stdin=subprocess.DEVNULL,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
        shell=False,
        creationflags=creationflags,
        **popen_kwargs,
    )

    return ClaudeRemoteStartResult(
        command=command,
        session_name=normalized_session_name,
        pid=process.pid,
    )
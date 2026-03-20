# src\claude_orchestrator\gui\claude_runner.py
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import re
import shutil
import subprocess
import sys
import time


BRIDGE_URL_PATTERN = re.compile(r"https://claude\.ai/code\?bridge=\S+")


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
    bridge_url: str
    log_path: str
    spawn_mode: str
    permission_mode: str


def _resolve_claude_path() -> Path:
    claude_path = shutil.which("claude.cmd") or shutil.which("claude")
    if not claude_path:
        raise FileNotFoundError(
            "claude command not found. Ensure Claude CLI is in PATH."
        )
    return Path(claude_path).resolve()


def start_claude_remote_control_session(
    *,
    repo_path: str,
    session_name: str,
    spawn_mode: str = "same-dir",
    permission_mode: str = "default",
) -> ClaudeRemoteStartResult:
    claude_path = _resolve_claude_path()

    repo_root = Path(repo_path).resolve()

    normalized_session_name = session_name.strip() or "orchestrator-remote"
    normalized_spawn_mode = spawn_mode.strip() or "same-dir"
    normalized_permission_mode = permission_mode.strip() or "default"

    command = [
        str(claude_path),
        "remote-control",
        "--name",
        normalized_session_name,
        "--spawn",
        normalized_spawn_mode,
        "--permission-mode",
        normalized_permission_mode,
    ]

    # Windowsはcmdで起動（これが安定）
    if sys.platform.startswith("win"):
        cmd_command = [
            "cmd",
            "/k",  # 終了させない
            str(claude_path),
            "remote-control",
            "--name",
            normalized_session_name,
            "--spawn",
            normalized_spawn_mode,
            "--permission-mode",
            normalized_permission_mode,
        ]

        process = subprocess.Popen(
            cmd_command,
            cwd=str(repo_root),
            creationflags=subprocess.CREATE_NEW_CONSOLE,
        )

        return ClaudeRemoteStartResult(
            command=command,
            session_name=normalized_session_name,
            pid=process.pid,
            bridge_url="",  # v1では未取得OK
            log_path="",
            spawn_mode=normalized_spawn_mode,
            permission_mode=normalized_permission_mode,
        )

    # Linux / Mac（現状維持）
    process = subprocess.Popen(
        command,
        cwd=str(repo_root),
        stdin=subprocess.DEVNULL,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
    )

    return ClaudeRemoteStartResult(
        command=command,
        session_name=normalized_session_name,
        pid=process.pid,
        bridge_url="",
        log_path="",
        spawn_mode=normalized_spawn_mode,
        permission_mode=normalized_permission_mode,
    )
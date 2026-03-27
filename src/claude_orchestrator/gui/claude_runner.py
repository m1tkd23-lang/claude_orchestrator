# src\claude_orchestrator\gui\claude_runner.py
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import os
import re
import shutil
import subprocess
import sys
import tempfile
import time


BRIDGE_URL_PATTERN = re.compile(r"https://claude\.ai/code\?bridge=\S+")
ENVIRONMENT_ID_PATTERN = re.compile(r"environment_id=(env_[A-Za-z0-9]+)")


@dataclass
class ClaudeRunResult:
    returncode: int
    stdout: str
    stderr: str
    command: list[str]
    timed_out: bool
    timeout_seconds: int


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
            "claude command not found. "
            "Ensure Claude CLI is installed and available in PATH."
        )
    return Path(claude_path).resolve()


def _build_windows_hidden_startupinfo() -> subprocess.STARTUPINFO | None:
    if not sys.platform.startswith("win"):
        return None

    startupinfo = subprocess.STARTUPINFO()
    startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
    startupinfo.wShowWindow = 0
    return startupinfo


def _build_windows_creationflags(*, new_console: bool = False) -> int:
    if not sys.platform.startswith("win"):
        return 0

    flags = 0
    flags |= getattr(subprocess, "CREATE_NO_WINDOW", 0)

    if new_console:
        flags |= getattr(subprocess, "CREATE_NEW_CONSOLE", 0)

    return flags


def run_claude_print_mode(
    *,
    repo_path: str,
    prompt_text: str,
    timeout_seconds: int = 300,
    output_json_path: str | None = None,
    poll_interval_seconds: float = 0.5,
    report_detect_grace_seconds: float = 2.0,
) -> ClaudeRunResult:
    claude_path = _resolve_claude_path()
    repo_root = Path(repo_path).resolve()
    report_path = Path(output_json_path).resolve() if output_json_path else None

    command = [
        str(claude_path),
        "-p",
        "--permission-mode",
        "bypassPermissions",
    ]

    stdout_temp_path = ""
    stderr_temp_path = ""

    try:
        with tempfile.NamedTemporaryFile(
            delete=False,
            suffix=".claude_stdout.log",
        ) as stdout_tmp:
            stdout_temp_path = stdout_tmp.name
        with tempfile.NamedTemporaryFile(
            delete=False,
            suffix=".claude_stderr.log",
        ) as stderr_tmp:
            stderr_temp_path = stderr_tmp.name

        with open(stdout_temp_path, "wb") as stdout_file, open(
            stderr_temp_path,
            "wb",
        ) as stderr_file:
            process = subprocess.Popen(
                command,
                stdin=subprocess.PIPE,
                stdout=stdout_file,
                stderr=stderr_file,
                cwd=str(repo_root),
                shell=False,
                startupinfo=_build_windows_hidden_startupinfo(),
                creationflags=_build_windows_creationflags(new_console=False),
            )

            assert process.stdin is not None
            process.stdin.write(prompt_text.encode("utf-8", errors="replace"))
            process.stdin.close()

            started_at = time.time()
            report_detected_at: float | None = None
            timed_out = False

            while True:
                returncode = process.poll()
                report_exists = bool(report_path and report_path.exists())

                if report_exists and report_detected_at is None:
                    report_detected_at = time.time()

                if returncode is not None:
                    break

                elapsed = time.time() - started_at
                if elapsed >= timeout_seconds:
                    timed_out = True
                    _terminate_process(process)
                    try:
                        process.wait(timeout=5)
                    except subprocess.TimeoutExpired:
                        _kill_process(process)
                        process.wait(timeout=5)
                    break

                if report_detected_at is not None:
                    grace_elapsed = time.time() - report_detected_at
                    if grace_elapsed >= report_detect_grace_seconds:
                        _terminate_process(process)
                        try:
                            process.wait(timeout=5)
                        except subprocess.TimeoutExpired:
                            _kill_process(process)
                            process.wait(timeout=5)
                        break

                time.sleep(max(0.1, poll_interval_seconds))

            final_returncode = process.poll()
            if final_returncode is None:
                try:
                    final_returncode = process.wait(timeout=1)
                except subprocess.TimeoutExpired:
                    _kill_process(process)
                    final_returncode = process.wait(timeout=5)

        stdout_text = Path(stdout_temp_path).read_text(
            encoding="utf-8",
            errors="replace",
        )
        stderr_text = Path(stderr_temp_path).read_text(
            encoding="utf-8",
            errors="replace",
        )

        return ClaudeRunResult(
            returncode=int(final_returncode if final_returncode is not None else -1),
            stdout=stdout_text,
            stderr=stderr_text,
            command=command,
            timed_out=timed_out,
            timeout_seconds=timeout_seconds,
        )
    finally:
        if stdout_temp_path:
            try:
                os.unlink(stdout_temp_path)
            except OSError:
                pass
        if stderr_temp_path:
            try:
                os.unlink(stderr_temp_path)
            except OSError:
                pass


def start_claude_remote_control_session(
    *,
    repo_path: str,
    session_name: str,
    spawn_mode: str = "same-dir",
    permission_mode: str = "default",
    url_wait_seconds: float = 15.0,
) -> ClaudeRemoteStartResult:
    claude_path = _resolve_claude_path()

    repo_root = Path(repo_path).resolve()
    normalized_session_name = str(session_name).strip() or "orchestrator-remote"
    normalized_spawn_mode = str(spawn_mode).strip() or "same-dir"
    normalized_permission_mode = str(permission_mode).strip() or "default"

    log_path = _build_remote_log_path(
        repo_path=repo_root,
        session_name=normalized_session_name,
    )
    log_path.parent.mkdir(parents=True, exist_ok=True)
    log_path.write_text("", encoding="utf-8")

    command = [
        str(claude_path),
        "remote-control",
        "--name",
        normalized_session_name,
        "--spawn",
        normalized_spawn_mode,
        "--permission-mode",
        normalized_permission_mode,
        "--debug-file",
        str(log_path),
    ]

    if sys.platform.startswith("win"):
        cmdline = _build_windows_cmdline(command)
        process = subprocess.Popen(
            ["cmd", "/k", cmdline],
            cwd=str(repo_root),
            shell=False,
            creationflags=subprocess.CREATE_NEW_CONSOLE,
        )

        bridge_url = _wait_for_bridge_url_from_log(
            log_path=log_path,
            wait_seconds=url_wait_seconds,
        )

        return ClaudeRemoteStartResult(
            command=command,
            session_name=normalized_session_name,
            pid=process.pid,
            bridge_url=bridge_url,
            log_path=str(log_path),
            spawn_mode=normalized_spawn_mode,
            permission_mode=normalized_permission_mode,
        )

    process = subprocess.Popen(
        command,
        cwd=str(repo_root),
        stdin=subprocess.DEVNULL,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        encoding="utf-8",
        errors="replace",
        shell=False,
    )

    bridge_url = ""
    started_at = time.time()

    if process.stdout is not None:
        while time.time() - started_at < url_wait_seconds:
            line = process.stdout.readline()
            if not line:
                if process.poll() is not None:
                    break
                time.sleep(0.1)
                continue

            with log_path.open("a", encoding="utf-8") as f:
                f.write(line)

            bridge_url = _extract_bridge_url(line)
            if bridge_url:
                break

    if not bridge_url:
        bridge_url = _wait_for_bridge_url_from_log(
            log_path=log_path,
            wait_seconds=max(1.0, url_wait_seconds / 2.0),
        )

    return ClaudeRemoteStartResult(
        command=command,
        session_name=normalized_session_name,
        pid=process.pid,
        bridge_url=bridge_url,
        log_path=str(log_path),
        spawn_mode=normalized_spawn_mode,
        permission_mode=normalized_permission_mode,
    )


def _build_remote_log_path(
    *,
    repo_path: Path,
    session_name: str,
) -> Path:
    runtime_dir = repo_path / ".claude_orchestrator" / "runtime" / "remote_logs"
    safe_session_name = re.sub(
        r"[^A-Za-z0-9_.-]+",
        "_",
        session_name.strip() or "remote",
    )
    timestamp = time.strftime("%Y%m%d-%H%M%S")
    return runtime_dir / f"{safe_session_name}_{timestamp}.log"


def _build_windows_cmdline(command: list[str]) -> str:
    return subprocess.list2cmdline(command)


def _wait_for_bridge_url_from_log(
    *,
    log_path: Path,
    wait_seconds: float,
) -> str:
    started_at = time.time()
    last_text = ""

    while time.time() - started_at < wait_seconds:
        if log_path.exists():
            text = log_path.read_text(encoding="utf-8", errors="replace")
            if text != last_text:
                last_text = text
                bridge_url = _extract_bridge_url(text)
                if bridge_url:
                    return bridge_url
        time.sleep(0.2)

    return ""


def _extract_bridge_url(text: str) -> str:
    direct_match = BRIDGE_URL_PATTERN.search(text)
    if direct_match:
        return direct_match.group(0)

    env_match = ENVIRONMENT_ID_PATTERN.search(text)
    if env_match:
        environment_id = env_match.group(1)
        return f"https://claude.ai/code?bridge={environment_id}"

    return ""


def _terminate_process(process: subprocess.Popen) -> None:
    try:
        process.terminate()
    except OSError:
        pass


def _kill_process(process: subprocess.Popen) -> None:
    try:
        process.kill()
    except OSError:
        pass
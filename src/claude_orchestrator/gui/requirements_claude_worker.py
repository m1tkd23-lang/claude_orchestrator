# src\claude_orchestrator\gui\requirements_claude_worker.py
from __future__ import annotations

from dataclasses import dataclass
import json
import re

from PySide6.QtCore import QObject, Signal

from claude_orchestrator.gui.claude_runner import run_claude_print_mode


_CODE_FENCE_JSON_PATTERN = re.compile(
    r"```(?:json)?\s*(\{.*\})\s*```",
    re.DOTALL,
)


@dataclass
class RequirementsClaudeWorkerResult:
    suggested_requirements_json: dict
    raw_stdout: str
    raw_stderr: str
    returncode: int
    timed_out: bool
    timeout_seconds: int


class RequirementsClaudeWorker(QObject):
    result_ready = Signal(object)
    log_message = Signal(str)
    error_signal = Signal(str, str)
    finished = Signal()

    def __init__(
        self,
        *,
        repo_path: str,
        prompt_text: str,
        timeout_seconds: int = 300,
    ) -> None:
        super().__init__()
        self.repo_path = repo_path
        self.prompt_text = prompt_text
        self.timeout_seconds = timeout_seconds

    def run(self) -> None:
        try:
            self.log_message.emit("[INFO] requirements Claude suggestion started")
            result = run_claude_print_mode(
                repo_path=self.repo_path,
                prompt_text=self.prompt_text,
                timeout_seconds=self.timeout_seconds,
            )

            if result.timed_out:
                raise RuntimeError(
                    f"Claude execution timed out after {result.timeout_seconds} seconds."
                )

            json_text = _extract_json_object_text(result.stdout)
            if not json_text:
                raise RuntimeError(
                    "Claude output did not contain a JSON object.\n"
                    f"stdout:\n{result.stdout}\n\nstderr:\n{result.stderr}"
                )

            try:
                parsed = json.loads(json_text)
            except json.JSONDecodeError as exc:
                raise RuntimeError(
                    "Claude returned invalid JSON.\n"
                    f"stdout:\n{result.stdout}\n\nstderr:\n{result.stderr}"
                ) from exc

            if not isinstance(parsed, dict):
                raise RuntimeError("Claude returned JSON that is not an object root.")

            self.result_ready.emit(
                RequirementsClaudeWorkerResult(
                    suggested_requirements_json=parsed,
                    raw_stdout=result.stdout,
                    raw_stderr=result.stderr,
                    returncode=result.returncode,
                    timed_out=result.timed_out,
                    timeout_seconds=result.timeout_seconds,
                )
            )
            self.log_message.emit("[INFO] requirements Claude suggestion completed")
        except Exception as exc:
            self.error_signal.emit(
                "requirements Claude実行エラー",
                f"{type(exc).__name__}: {exc}",
            )
        finally:
            self.finished.emit()


def _extract_json_object_text(text: str) -> str:
    stripped = text.strip()
    if not stripped:
        return ""

    fenced_match = _CODE_FENCE_JSON_PATTERN.search(stripped)
    if fenced_match:
        candidate = fenced_match.group(1).strip()
        if _is_valid_json_object_text(candidate):
            return candidate

    if _is_valid_json_object_text(stripped):
        return stripped

    first_brace = stripped.find("{")
    if first_brace == -1:
        return ""

    decoder = json.JSONDecoder()
    for start_index in range(first_brace, len(stripped)):
        if stripped[start_index] != "{":
            continue
        try:
            value, end_index = decoder.raw_decode(stripped[start_index:])
        except json.JSONDecodeError:
            continue

        if isinstance(value, dict):
            return stripped[start_index : start_index + end_index].strip()

    return ""


def _is_valid_json_object_text(text: str) -> bool:
    try:
        value = json.loads(text)
    except json.JSONDecodeError:
        return False
    return isinstance(value, dict)
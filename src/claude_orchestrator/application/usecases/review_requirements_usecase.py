# src\claude_orchestrator\application\usecases\review_requirements_usecase.py
from __future__ import annotations

import json
from pathlib import Path
import re
from typing import Any

from claude_orchestrator.gui.claude_runner import run_claude_print_mode
from claude_orchestrator.gui.services.review_requirements_prompt_service import (
    build_review_requirements_prompt,
)
from claude_orchestrator.infrastructure.project_paths import ProjectPaths
from claude_orchestrator.infrastructure.requirements_runtime import (
    RequirementsRuntime,
)


_CODE_FENCE_JSON_PATTERN = re.compile(
    r"```(?:json)?\s*(\{.*\})\s*```",
    re.DOTALL,
)


class ReviewRequirementsUseCase:
    def execute(self, repo_path: str) -> dict[str, Any]:
        target_repo = Path(repo_path).resolve()

        project_paths = ProjectPaths(target_repo=target_repo)
        project_paths.ensure_initialized()

        runtime = RequirementsRuntime(repo_root=target_repo)
        requirements_json = runtime.load_requirements_json()

        schema_path = (
            target_repo
            / ".claude_orchestrator"
            / "schemas"
            / "requirements_review.schema.json"
        )

        if not schema_path.exists():
            raise FileNotFoundError(
                f"requirements_review.schema.json not found: {schema_path}"
            )

        schema_text = schema_path.read_text(encoding="utf-8")

        prompt = build_review_requirements_prompt(
            repo_path=str(target_repo),
            requirements_json=requirements_json,
            schema_text=schema_text,
        )

        result = run_claude_print_mode(
            repo_path=str(target_repo),
            prompt_text=prompt,
        )

        if result.returncode != 0:
            raise RuntimeError(
                f"Claude execution failed: returncode={result.returncode}\n{result.stderr}"
            )

        review_json_text = _extract_json_object_text(result.stdout)
        if not review_json_text:
            raise ValueError(
                "Failed to parse review JSON.\n"
                f"stdout:\n{result.stdout}"
            )

        try:
            review_json = json.loads(review_json_text)
        except json.JSONDecodeError as exc:
            raise ValueError(
                "Failed to parse review JSON.\n"
                f"stdout:\n{result.stdout}"
            ) from exc

        if not isinstance(review_json, dict):
            raise ValueError("Review JSON root must be an object.")

        return {
            "ok": True,
            "review": review_json,
            "stdout": result.stdout,
            "stderr": result.stderr,
        }


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
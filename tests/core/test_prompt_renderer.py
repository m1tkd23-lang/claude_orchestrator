# tests\core\test_prompt_renderer.py
from __future__ import annotations

from claude_orchestrator.core.prompt_renderer import render_prompt


def test_render_prompt_replaces_known_placeholders_only() -> None:
    template = "task={task_id}, path={output_json_path}"
    result = render_prompt(
        template,
        task_id="TASK-0014",
        output_json_path="D:/repo/out.json",
    )
    assert result == "task=TASK-0014, path=D:/repo/out.json"


def test_render_prompt_keeps_unknown_placeholder_as_is() -> None:
    template = "director_report_v{N}.json / task={task_id}"
    result = render_prompt(template, task_id="TASK-0014")
    assert result == "director_report_v{N}.json / task=TASK-0014"


def test_render_prompt_keeps_json_like_text_untouched() -> None:
    template = '{"fixed": true, "task": "{task_id}"}'
    result = render_prompt(template, task_id="TASK-0014")
    assert result == '{"fixed": true, "task": "TASK-0014"}'


def test_render_prompt_keeps_carry_over_example_when_key_is_missing() -> None:
    template = "[carry_over from {task_id}] and [carry_over from {source_task_id}]"
    result = render_prompt(template, task_id="TASK-0014")
    assert result == "[carry_over from TASK-0014] and [carry_over from {source_task_id}]"
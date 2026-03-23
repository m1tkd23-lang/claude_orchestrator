# src\claude_orchestrator\gui\helpers\pipeline_summary_helpers.py
from __future__ import annotations

import json
from pathlib import Path
from typing import Any

_STANDARD_ROLES = ["task_router", "implementer", "reviewer", "director"]


def build_pipeline_task_summary(window: Any) -> dict[str, str]:
    task_id = _get_task_id(window)

    return {
        "task_id": task_id,
        "title": _get_text_attr(window, "detail_title", "current_task_title_edit"),
        "status": _get_text_attr(window, "detail_status", "current_task_status_edit"),
        "current_stage": _get_text_attr(window, "detail_current_stage"),
        "next_role": _get_text_attr(
            window,
            "detail_next_role",
            "current_task_next_role_edit",
        ),
        "cycle": _get_text_attr(
            window,
            "detail_cycle",
            "current_task_cycle_edit",
            "execution_cycle_edit",
        ),
        "last_completed_role": _get_text_attr(window, "detail_last_completed_role"),
        "planner_role": _get_current_planner_role(window),
        "post_flow_status": detect_post_flow_status(window),
        "stop_reservation": (
            "あり"
            if bool(getattr(window, "_stop_after_current_task_requested", False))
            else "なし"
        ),
    }


def build_pipeline_role_states(window: Any) -> list[dict[str, str]]:
    repo_path = _get_repo_path(window)
    task_id = _get_task_id(window)
    reports = load_standard_role_reports(repo_path, task_id)
    latest_reports = _latest_standard_reports_by_role(reports)

    result: list[dict[str, str]] = []
    for role in _STANDARD_ROLES:
        result.append(_build_standard_role_state(window, role, latest_reports.get(role)))

    result.append(_build_planner_role_state(window))
    result.append(_build_plan_director_role_state(window))
    return result


def build_pipeline_report_summaries(window: Any) -> dict[str, str]:
    repo_path = _get_repo_path(window)
    task_id = _get_task_id(window)
    reports = load_standard_role_reports(repo_path, task_id)
    latest_reports = _latest_standard_reports_by_role(reports)

    result: dict[str, str] = {}
    for role in _STANDARD_ROLES:
        latest_report = latest_reports.get(role)
        if role == "task_router":
            result[role] = summarize_task_router_report(latest_report)
        else:
            result[role] = summarize_latest_standard_report(latest_report)

    planner_report = getattr(window, "_planner_report", None)
    planner_state_store = getattr(window, "_planner_state_store", None)
    planner_role = _get_current_planner_role(window)
    plan_director_report = getattr(window, "_plan_director_report", None)

    result["planner"] = summarize_planner_report(
        planner_report,
        planner_state_store,
        planner_role,
    )
    result["plan_director"] = summarize_plan_director_report(
        plan_director_report,
        planner_report,
    )
    return result


def detect_post_flow_status(window: Any) -> str:
    execution_status = _get_text_attr(window, "execution_status_edit")
    execution_step = _get_text_attr(window, "execution_step_edit")

    if bool(getattr(window, "_planner_active", False)):
        return f"{_get_current_planner_role(window)} 実行中"

    if bool(getattr(window, "_plan_director_active", False)):
        return "plan_director 実行中"

    if bool(getattr(window, "_waiting_next_task_approval", False)):
        return "次task承認待ち"

    if bool(getattr(window, "_pending_auto_plan_director_after_planner", False)):
        return "plan_director 待機中"

    if bool(getattr(window, "_pending_auto_planner_after_completion", False)):
        return f"{_get_current_planner_role(window)} 待機中"

    if execution_status == "failed":
        return "異常終了"

    if execution_step == "stopped after current task":
        return "停止予約により後工程停止"

    if execution_step == "next task skipped":
        return "次task作成見送り"

    if execution_step == "next task already created":
        return "次task作成済み"

    if execution_step == "post-planning done":
        return "後工程完了"

    return "後工程なし"


def load_standard_role_reports(repo_path: str, task_id: str) -> list[dict]:
    if not repo_path or not task_id:
        return []

    inbox_dir = Path(repo_path) / ".claude_orchestrator" / "tasks" / task_id / "inbox"
    if not inbox_dir.exists():
        return []

    reports: list[dict] = []
    for json_path in inbox_dir.glob("*.json"):
        try:
            data = json.loads(json_path.read_text(encoding="utf-8"))
        except Exception:
            continue

        role = str(data.get("role", "")).strip()
        if role in _STANDARD_ROLES:
            reports.append(data)

    reports.sort(
        key=lambda report: (
            _safe_int(report.get("cycle"), 0),
            _STANDARD_ROLES.index(str(report.get("role", "")).strip())
            if str(report.get("role", "")).strip() in _STANDARD_ROLES
            else len(_STANDARD_ROLES),
        )
    )
    return reports


def summarize_latest_standard_report(report: dict | None) -> str:
    if not isinstance(report, dict):
        return "(report なし)"

    status = str(
        report.get("status", report.get("decision", report.get("final_action", "")))
    ).strip()
    summary = str(report.get("summary", "")).strip()
    cycle = str(report.get("cycle", "")).strip()

    lines: list[str] = []
    if status:
        lines.append(f"status: {status}")
    if cycle:
        lines.append(f"cycle: {cycle}")
    if lines:
        lines.append("")
    lines.append(summary if summary else "(summary なし)")
    return "\n".join(lines).strip()


def summarize_task_router_report(report: dict | None) -> str:
    if not isinstance(report, dict):
        return "(report なし)"

    lines: list[str] = []

    status = str(report.get("status", "")).strip()
    cycle = str(report.get("cycle", "")).strip()
    task_type = str(report.get("task_type", "")).strip()
    risk_level = str(report.get("risk_level", "")).strip()

    if status:
        lines.append(f"status: {status}")
    if cycle:
        lines.append(f"cycle: {cycle}")
    if task_type:
        lines.append(f"task_type: {task_type}")
    if risk_level:
        lines.append(f"risk_level: {risk_level}")

    role_skill_plan = report.get("role_skill_plan", {}) or {}
    if isinstance(role_skill_plan, dict):
        implementer_skills = _stringify_skill_list(role_skill_plan.get("implementer"))
        reviewer_skills = _stringify_skill_list(role_skill_plan.get("reviewer"))
        director_skills = _stringify_skill_list(role_skill_plan.get("director"))

        if implementer_skills:
            lines.append(f"implementer_skills: {implementer_skills}")
        if reviewer_skills:
            lines.append(f"reviewer_skills: {reviewer_skills}")
        if director_skills:
            lines.append(f"director_skills: {director_skills}")

    used_skills = _stringify_skill_list(report.get("used_skills"))
    if used_skills:
        lines.append(f"used_skills: {used_skills}")

    summary = str(report.get("summary", "")).strip()
    skill_selection_reasons = _normalize_string_list(report.get("skill_selection_reason"))
    initial_execution_notes = _normalize_string_list(report.get("initial_execution_notes"))

    body_sections: list[str] = []

    if summary:
        body_sections.append(summary)

    if skill_selection_reasons:
        body_sections.append(
            "skill_selection_reason:\n" + _format_bullets(skill_selection_reasons[:2])
        )

    if initial_execution_notes:
        body_sections.append(
            "initial_execution_notes:\n" + _format_bullets(initial_execution_notes[:2])
        )

    if body_sections:
        lines.append("")
        lines.append("\n\n".join(body_sections))
    elif not lines:
        lines.append("(task_router report 情報なし)")

    return "\n".join(lines).strip()


def summarize_planner_report(
    planner_report: dict | None,
    state_store: object | None,
    planner_role: str,
) -> str:
    if not isinstance(planner_report, dict):
        return "(planner report なし)"

    summary = str(planner_report.get("summary", "")).strip()
    proposals = planner_report.get("proposals", []) or []

    counts = {
        "proposed": 0,
        "accepted": 0,
        "rejected": 0,
        "deferred": 0,
        "task_created": 0,
    }

    state_map: dict[str, str] = {}
    getter = getattr(state_store, "get_state_map", None)
    if callable(getter):
        try:
            state_map = getter()
        except Exception:
            state_map = {}

    for proposal in proposals:
        proposal_id = str(proposal.get("proposal_id", "")).strip()
        state = state_map.get(proposal_id, "proposed")
        if state not in counts:
            counts["proposed"] += 1
            continue
        counts[state] += 1

    lines = [
        f"planner_role: {planner_role}",
        f"proposals: {len(proposals)}",
        (
            "accepted: "
            f"{counts['accepted']} / rejected: {counts['rejected']} / "
            f"deferred: {counts['deferred']} / task_created: {counts['task_created']}"
        ),
        "",
        summary if summary else "(summary なし)",
    ]
    return "\n".join(lines).strip()


def summarize_plan_director_report(
    plan_director_report: dict | None,
    planner_report: dict | None = None,
) -> str:
    if not isinstance(plan_director_report, dict):
        return "(plan_director report なし)"

    decision = str(plan_director_report.get("decision", "")).strip()
    selected_proposal_id = str(
        plan_director_report.get("selected_proposal_id", "") or ""
    ).strip()
    selected_planner_role = str(
        plan_director_report.get("selected_planner_role", "") or ""
    ).strip()
    selection_reason = str(plan_director_report.get("selection_reason", "")).strip()

    proposal = _find_selected_proposal(planner_report, selected_proposal_id)

    lines: list[str] = []
    if decision:
        lines.append(f"decision: {decision}")
    if selected_proposal_id:
        lines.append(f"selected_proposal_id: {selected_proposal_id}")
    if selected_planner_role:
        lines.append(f"selected_planner_role: {selected_planner_role}")

    if isinstance(proposal, dict):
        title = str(proposal.get("title", "")).strip()
        description = str(proposal.get("description", "")).strip()
        why_now = str(proposal.get("why_now", "")).strip()
        depends_on = _normalize_string_list(proposal.get("depends_on"))

        if title:
            lines.append(f"title: {title}")

        if description:
            lines.append("")
            lines.append("description:")
            lines.append(description)

        if why_now:
            lines.append("")
            lines.append("why_now:")
            lines.append(why_now)

        if depends_on:
            lines.append("")
            lines.append("depends_on:")
            lines.append(", ".join(depends_on))

    if selection_reason:
        lines.append("")
        lines.append("selection_reason:")
        lines.append(selection_reason)

    if not lines:
        return "(plan_director report 情報なし)"
    return "\n".join(lines).strip()


def _build_standard_role_state(
    window: Any,
    role: str,
    latest_report: dict | None,
) -> dict[str, str]:
    execution_status = _get_text_attr(window, "execution_status_edit")
    execution_role = _get_text_attr(window, "execution_role_edit")
    next_role = _get_text_attr(window, "detail_next_role", "current_task_next_role_edit")
    cycle_text = _get_text_attr(
        window,
        "execution_cycle_edit",
        "detail_cycle",
        "current_task_cycle_edit",
    )
    busy = _is_pipeline_busy(window)

    state = "idle"
    note = "-"

    if execution_status == "failed" and execution_role == role:
        state = "failed"
        note = f"cycle {cycle_text}" if cycle_text else "failed"
    elif busy and execution_role == role:
        state = "running"
        note = f"cycle {cycle_text}" if cycle_text else "running"
    elif next_role == role:
        state = "waiting"
        note = "next"
    elif isinstance(latest_report, dict):
        state = "done"
        report_cycle = str(latest_report.get("cycle", "")).strip()
        note = f"cycle {report_cycle}" if report_cycle else "done"

    return {
        "role": role,
        "state": state,
        "note": note,
    }


def _build_planner_role_state(window: Any) -> dict[str, str]:
    execution_status = _get_text_attr(window, "execution_status_edit")
    execution_role = _get_text_attr(window, "execution_role_edit")
    execution_step = _get_text_attr(window, "execution_step_edit")
    planner_role = _get_current_planner_role(window)

    state = "idle"
    note = "-"

    if execution_status == "failed" and execution_role in {
        "planner",
        "planner_safe",
        "planner_improvement",
    }:
        state = "failed"
        note = planner_role
    elif bool(getattr(window, "_planner_active", False)):
        state = "running"
        note = planner_role
    elif bool(getattr(window, "_pending_auto_planner_after_completion", False)):
        state = "waiting"
        note = "queued"
    elif execution_step == "stopped after current task":
        state = "stopped"
        note = "skipped"
    elif isinstance(getattr(window, "_planner_report", None), dict):
        state = "done"
        note = planner_role

    return {
        "role": "planner",
        "state": state,
        "note": note,
    }


def _build_plan_director_role_state(window: Any) -> dict[str, str]:
    execution_status = _get_text_attr(window, "execution_status_edit")
    execution_role = _get_text_attr(window, "execution_role_edit")

    state = "idle"
    note = "-"

    report = getattr(window, "_plan_director_report", None)
    decision = ""
    if isinstance(report, dict):
        decision = str(report.get("decision", "")).strip()

    if execution_status == "failed" and execution_role == "plan_director":
        state = "failed"
        note = "failed"
    elif bool(getattr(window, "_plan_director_active", False)):
        state = "running"
        note = "running"
    elif bool(getattr(window, "_waiting_next_task_approval", False)):
        state = "approval"
        note = "approval"
    elif isinstance(report, dict):
        state = "done"
        note = decision or "done"

    return {
        "role": "plan_director",
        "state": state,
        "note": note,
    }


def _latest_standard_reports_by_role(reports: list[dict]) -> dict[str, dict]:
    result: dict[str, dict] = {}
    for report in reports:
        role = str(report.get("role", "")).strip()
        if role in _STANDARD_ROLES:
            result[role] = report
    return result


def _find_selected_proposal(
    planner_report: dict | None,
    selected_proposal_id: str,
) -> dict | None:
    if not isinstance(planner_report, dict):
        return None

    normalized = str(selected_proposal_id).strip()
    if not normalized:
        return None

    proposals = planner_report.get("proposals", []) or []
    for proposal in proposals:
        if str(proposal.get("proposal_id", "")).strip() == normalized:
            return proposal
    return None


def _stringify_skill_list(value: object) -> str:
    items = _normalize_string_list(value)
    return ", ".join(items)


def _normalize_string_list(value: object) -> list[str]:
    if not isinstance(value, list):
        return []

    result: list[str] = []
    for item in value:
        text = str(item).strip()
        if text:
            result.append(text)
    return result


def _format_bullets(items: list[str]) -> str:
    return "\n".join(f"- {item}" for item in items if str(item).strip())


def _get_current_planner_role(window: Any) -> str:
    combo = getattr(window, "planner_role_combo", None)
    if combo is not None:
        current_data = combo.currentData()
        if isinstance(current_data, str) and current_data in {
            "planner_safe",
            "planner_improvement",
        }:
            return current_data

        current_text = str(combo.currentText()).strip()
        if current_text in {"planner_safe", "planner_improvement"}:
            return current_text

    planner_role = str(getattr(window, "_planner_role", "planner_safe")).strip()
    if planner_role not in {"planner_safe", "planner_improvement"}:
        return "planner_safe"
    return planner_role


def _get_repo_path(window: Any) -> str:
    repo_path_edit = getattr(window, "repo_path_edit", None)
    if repo_path_edit is None:
        return ""
    text_getter = getattr(repo_path_edit, "text", None)
    if not callable(text_getter):
        return ""
    return str(text_getter()).strip()


def _get_task_id(window: Any) -> str:
    active_task_id = str(getattr(window, "_active_pipeline_task_id", "")).strip()
    if active_task_id:
        return active_task_id

    selected_task_id = str(getattr(window, "_selected_task_id", "")).strip()
    if selected_task_id:
        return selected_task_id

    current_task_id = str(getattr(window, "_current_task_id", "")).strip()
    if current_task_id:
        return current_task_id

    return _get_text_attr(window, "detail_task_id", "current_task_id_edit")


def _get_text_attr(window: Any, *attr_names: str) -> str:
    for attr_name in attr_names:
        widget = getattr(window, attr_name, None)
        if widget is None:
            continue
        getter = getattr(widget, "text", None)
        if callable(getter):
            text = str(getter()).strip()
            if text:
                return text
    return ""


def _is_pipeline_busy(window: Any) -> bool:
    checker = getattr(window, "_is_pipeline_busy", None)
    if callable(checker):
        try:
            return bool(checker())
        except Exception:
            return False

    return bool(
        getattr(window, "_auto_run_active", False)
        or getattr(window, "_planner_active", False)
        or getattr(window, "_plan_director_active", False)
        or getattr(window, "_pending_auto_planner_after_completion", False)
        or getattr(window, "_pending_auto_plan_director_after_planner", False)
        or getattr(window, "_waiting_next_task_approval", False)
    )


def _safe_int(value: object, default: int) -> int:
    try:
        return int(value)  # type: ignore[arg-type]
    except Exception:
        return default
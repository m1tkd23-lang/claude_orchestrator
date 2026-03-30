# src\claude_orchestrator\services\requirements_context_compactor.py
from __future__ import annotations

from typing import Any


_FEATURE_STATUS_PRIORITY = {
    "partial": 0,
    "not_implemented": 1,
    "gui_unconnected": 2,
    "implemented": 3,
    "gui_connected": 4,
    "out_of_scope": 5,
}

_SUPPORTED_MODES = {
    "requirements_authoring",
    "docs_generation",
    "planning",
    "implementation_seed",
}


def build_requirements_context(
    requirements: dict[str, Any],
    mode: str,
    *,
    max_feature_groups: int | None = None,
    max_completion_sections: int | None = None,
    max_features: int | None = None,
) -> str:
    """requirements.json を Claude 向け compact text に変換する."""

    normalized_mode = str(mode).strip()
    if normalized_mode not in _SUPPORTED_MODES:
        raise ValueError(f"unsupported requirements context mode: {mode}")

    if normalized_mode == "requirements_authoring":
        return _build_requirements_authoring_context(
            requirements,
            max_feature_groups=max_feature_groups,
        )

    if normalized_mode == "docs_generation":
        return _build_docs_generation_context(
            requirements,
            max_feature_groups=max_feature_groups,
            max_completion_sections=max_completion_sections,
        )

    if normalized_mode == "planning":
        return _build_planning_context(
            requirements,
            max_feature_groups=max_feature_groups,
            max_completion_sections=max_completion_sections,
            max_features=max_features,
        )

    return _build_implementation_seed_context(
        requirements,
        max_features=max_features,
    )


def _build_requirements_authoring_context(
    requirements: dict[str, Any],
    *,
    max_feature_groups: int | None,
) -> str:
    sections: list[str] = []

    sections.append(
        _render_section(
            "Project Name",
            [_as_non_empty_string(requirements.get("project_name"))],
        )
    )
    sections.append(
        _render_section(
            "Requirement Status",
            [_as_non_empty_string(requirements.get("requirement_status"))],
        )
    )
    sections.append(
        _render_section(
            "Product Summary",
            [_as_non_empty_string(requirements.get("product_summary"))],
        )
    )
    sections.append(
        _render_section(
            "Core Purpose",
            [_as_non_empty_string(requirements.get("core_purpose"))],
        )
    )
    sections.append(
        _render_section(
            "Target Users",
            _render_string_list(_as_string_list(requirements.get("target_users"))),
        )
    )
    sections.append(
        _render_section(
            "Main Roles",
            _render_string_list(_as_string_list(requirements.get("main_roles"))),
        )
    )
    sections.append(
        _render_section(
            "Usage Modes",
            _render_string_list(_as_string_list(requirements.get("usage_modes"))),
        )
    )
    sections.append(
        _render_section(
            "Key Value Points",
            _render_string_list(_as_string_list(requirements.get("value_points"))),
        )
    )
    sections.append(
        _render_section(
            "MVP Feature Groups",
            _render_mvp_feature_groups(
                requirements.get("mvp_feature_groups"),
                max_items=max_feature_groups,
                include_completion_refs=True,
            ),
        )
    )
    sections.append(
        _render_section(
            "Constraints",
            _render_string_list(_as_string_list(requirements.get("constraints"))),
        )
    )
    sections.append(
        _render_section(
            "Out of Scope",
            _render_string_list(_as_string_list(requirements.get("out_of_scope"))),
        )
    )
    sections.append(
        _render_section(
            "Open Questions",
            _render_string_list(_as_string_list(requirements.get("open_questions"))),
        )
    )

    return _join_sections(sections)


def _build_docs_generation_context(
    requirements: dict[str, Any],
    *,
    max_feature_groups: int | None,
    max_completion_sections: int | None,
) -> str:
    sections: list[str] = []

    sections.append(
        _render_section(
            "Project Name",
            [_as_non_empty_string(requirements.get("project_name"))],
        )
    )
    sections.append(
        _render_section(
            "Product Summary",
            [_as_non_empty_string(requirements.get("product_summary"))],
        )
    )
    sections.append(
        _render_section(
            "Core Purpose",
            [_as_non_empty_string(requirements.get("core_purpose"))],
        )
    )
    sections.append(
        _render_section(
            "Target Users",
            _render_string_list(_as_string_list(requirements.get("target_users"))),
        )
    )
    sections.append(
        _render_section(
            "Usage Modes",
            _render_string_list(_as_string_list(requirements.get("usage_modes"))),
        )
    )
    sections.append(
        _render_section(
            "MVP Feature Groups",
            _render_mvp_feature_groups(
                requirements.get("mvp_feature_groups"),
                max_items=max_feature_groups,
                include_completion_refs=True,
            ),
        )
    )
    sections.append(
        _render_section(
            "Main Flow",
            _render_numbered_string_list(_as_string_list(requirements.get("main_flow"))),
        )
    )
    sections.append(
        _render_section(
            "Technical Policy",
            _render_string_list(_as_string_list(requirements.get("technical_policy"))),
        )
    )
    sections.append(
        _render_section(
            "Design Principles",
            _render_string_list(_as_string_list(requirements.get("design_principles"))),
        )
    )
    sections.append(
        _render_section(
            "Constraints",
            _render_string_list(_as_string_list(requirements.get("constraints"))),
        )
    )
    sections.append(
        _render_section(
            "Out of Scope",
            _render_string_list(_as_string_list(requirements.get("out_of_scope"))),
        )
    )
    sections.append(
        _render_section(
            "MVP Completion Sections",
            _render_completion_sections(
                requirements.get("mvp_completion_sections"),
                max_items=max_completion_sections,
            ),
        )
    )
    sections.append(
        _render_section(
            "Priority Order",
            _render_numbered_string_list(
                _as_string_list(requirements.get("priority_order"))
            ),
        )
    )

    return _join_sections(sections)


def _build_planning_context(
    requirements: dict[str, Any],
    *,
    max_feature_groups: int | None,
    max_completion_sections: int | None,
    max_features: int | None,
) -> str:
    sections: list[str] = []

    sections.append(
        _render_section(
            "Core Purpose",
            [_as_non_empty_string(requirements.get("core_purpose"))],
        )
    )
    sections.append(
        _render_section(
            "MVP Feature Groups",
            _render_mvp_feature_groups(
                requirements.get("mvp_feature_groups"),
                max_items=max_feature_groups,
                include_completion_refs=True,
            ),
        )
    )
    sections.append(
        _render_section(
            "MVP Completion Sections",
            _render_completion_sections(
                requirements.get("mvp_completion_sections"),
                max_items=max_completion_sections,
            ),
        )
    )
    sections.append(
        _render_section(
            "Feature Inventory",
            _render_feature_inventory(
                requirements.get("feature_inventory"),
                max_items=max_features,
                prioritize_active_items=True,
            ),
        )
    )
    sections.append(
        _render_section(
            "Priority Order",
            _render_numbered_string_list(
                _as_string_list(requirements.get("priority_order"))
            ),
        )
    )
    sections.append(
        _render_section(
            "Constraints",
            _render_string_list(_as_string_list(requirements.get("constraints"))),
        )
    )
    sections.append(
        _render_section(
            "Out of Scope",
            _render_string_list(_as_string_list(requirements.get("out_of_scope"))),
        )
    )
    sections.append(
        _render_section(
            "Open Questions",
            _render_string_list(_as_string_list(requirements.get("open_questions"))),
        )
    )

    return _join_sections(sections)


def _build_implementation_seed_context(
    requirements: dict[str, Any],
    *,
    max_features: int | None,
) -> str:
    sections: list[str] = []

    sections.append(
        _render_section(
            "Core Purpose",
            [_as_non_empty_string(requirements.get("core_purpose"))],
        )
    )
    sections.append(
        _render_section(
            "Main Flow",
            _render_numbered_string_list(_as_string_list(requirements.get("main_flow"))),
        )
    )
    sections.append(
        _render_section(
            "Constraints",
            _render_string_list(_as_string_list(requirements.get("constraints"))),
        )
    )
    sections.append(
        _render_section(
            "Feature Inventory",
            _render_feature_inventory(
                requirements.get("feature_inventory"),
                max_items=max_features,
                prioritize_active_items=True,
            ),
        )
    )

    return _join_sections(sections)


def _render_mvp_feature_groups(
    value: Any,
    *,
    max_items: int | None,
    include_completion_refs: bool,
) -> list[str]:
    groups = _as_dict_list(value)
    if max_items is not None:
        groups = groups[:max_items]

    lines: list[str] = []
    for index, group in enumerate(groups, start=1):
        name = _as_non_empty_string(group.get("name"))
        summary = _as_non_empty_string(group.get("summary"))
        requirements = _as_string_list(group.get("requirements"))
        priority = _as_non_empty_string(group.get("priority"))
        completion_refs = _as_string_list(group.get("completion_section_refs"))

        title = name or f"feature_group_{index}"
        if priority:
            lines.append(f"{index}. {title} | priority: {priority}")
        else:
            lines.append(f"{index}. {title}")

        if summary:
            lines.append(f"  Summary: {summary}")

        if requirements:
            lines.append("  Requirements:")
            for item in requirements:
                lines.append(f"  - {item}")

        if include_completion_refs and completion_refs:
            lines.append("  Completion Section Refs:")
            for ref in completion_refs:
                lines.append(f"  - {ref}")

    return lines


def _render_completion_sections(
    value: Any,
    *,
    max_items: int | None,
) -> list[str]:
    sections = _as_dict_list(value)
    sections = sorted(
        sections,
        key=lambda item: _completion_section_sort_key(item),
    )
    if max_items is not None:
        sections = sections[:max_items]

    lines: list[str] = []
    for index, section in enumerate(sections, start=1):
        name = _as_non_empty_string(section.get("section_name"))
        goal = _as_non_empty_string(section.get("goal"))
        items = _as_string_list(section.get("completion_items"))
        priority = section.get("priority")
        judgement = _as_non_empty_string(section.get("judgement"))
        notes = _as_string_list(section.get("notes"))

        title = name or f"completion_section_{index}"
        meta_parts: list[str] = []
        if isinstance(priority, int):
            meta_parts.append(f"priority: {priority}")
        if judgement:
            meta_parts.append(f"judgement: {judgement}")

        if meta_parts:
            lines.append(f"{index}. {title} | " + " | ".join(meta_parts))
        else:
            lines.append(f"{index}. {title}")

        if goal:
            lines.append(f"  Goal: {goal}")

        if items:
            lines.append("  Completion Items:")
            for item in items:
                lines.append(f"  - {item}")

        if notes:
            lines.append("  Notes:")
            for note in notes:
                lines.append(f"  - {note}")

    return lines


def _render_feature_inventory(
    value: Any,
    *,
    max_items: int | None,
    prioritize_active_items: bool,
) -> list[str]:
    features = _as_dict_list(value)

    if prioritize_active_items:
        features = sorted(
            features,
            key=lambda item: _feature_inventory_sort_key(item),
        )

    if max_items is not None:
        features = features[:max_items]

    lines: list[str] = []
    for index, feature in enumerate(features, start=1):
        feature_name = _as_non_empty_string(feature.get("feature_name"))
        status = _as_non_empty_string(feature.get("status"))
        layers = _as_string_list(feature.get("layers"))
        summary = _as_non_empty_string(feature.get("summary"))
        completion_links = _as_string_list(feature.get("completion_links"))
        task_split_notes = _as_string_list(feature.get("task_split_notes"))
        related_files = _as_string_list(feature.get("related_files"))
        notes = _as_string_list(feature.get("notes"))

        title = feature_name or f"feature_{index}"
        header_parts: list[str] = []
        if status:
            header_parts.append(f"status: {status}")
        if layers:
            header_parts.append(f"layers: {', '.join(layers)}")

        if header_parts:
            lines.append(f"{index}. {title} | " + " | ".join(header_parts))
        else:
            lines.append(f"{index}. {title}")

        if summary:
            lines.append(f"  Summary: {summary}")

        if completion_links:
            lines.append("  Completion Links:")
            for link in completion_links:
                lines.append(f"  - {link}")

        if task_split_notes:
            lines.append("  Task Split Notes:")
            for note in task_split_notes:
                lines.append(f"  - {note}")

        if related_files:
            lines.append("  Related Files:")
            for file_path in related_files:
                lines.append(f"  - {file_path}")

        if notes:
            lines.append("  Notes:")
            for note in notes:
                lines.append(f"  - {note}")

    return lines


def _render_section(title: str, lines: list[str]) -> str:
    cleaned_lines = [line for line in lines if line.strip()]
    if not cleaned_lines:
        return ""
    return "\n".join([f"[{title}]", *cleaned_lines])


def _render_string_list(items: list[str]) -> list[str]:
    return [f"- {item}" for item in items if item.strip()]


def _render_numbered_string_list(items: list[str]) -> list[str]:
    return [f"{index}. {item}" for index, item in enumerate(items, start=1) if item.strip()]


def _join_sections(sections: list[str]) -> str:
    compact_sections = [section.strip() for section in sections if section.strip()]
    return "\n\n".join(compact_sections).strip()


def _completion_section_sort_key(item: dict[str, Any]) -> tuple[int, str]:
    priority = item.get("priority")
    if not isinstance(priority, int):
        priority = 9999
    name = _as_non_empty_string(item.get("section_name"))
    return (priority, name)


def _feature_inventory_sort_key(item: dict[str, Any]) -> tuple[int, str]:
    status = _as_non_empty_string(item.get("status"))
    priority = _FEATURE_STATUS_PRIORITY.get(status, 9999)
    feature_name = _as_non_empty_string(item.get("feature_name"))
    return (priority, feature_name)


def _as_string_list(value: Any) -> list[str]:
    if not isinstance(value, list):
        return []

    out: list[str] = []
    for item in value:
        if not isinstance(item, str):
            continue
        normalized = item.strip()
        if not normalized:
            continue
        out.append(normalized)
    return out


def _as_dict_list(value: Any) -> list[dict[str, Any]]:
    if not isinstance(value, list):
        return []

    out: list[dict[str, Any]] = []
    for item in value:
        if isinstance(item, dict):
            out.append(item)
    return out


def _as_non_empty_string(value: Any) -> str:
    if not isinstance(value, str):
        return ""
    return value.strip()
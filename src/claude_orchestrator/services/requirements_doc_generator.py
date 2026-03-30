# src\claude_orchestrator\services\requirements_doc_generator.py
from __future__ import annotations

from typing import Any


def generate_project_core_purpose_doc(requirements: dict[str, Any]) -> str:
    """requirements.json から 開発の目的本筋.md を生成する."""

    lines: list[str] = ["# 開発の目的本筋", ""]

    lines.extend(
        _section(
            "## 1. この開発で作るもの",
            _build_project_overview_lines(requirements),
        )
    )
    lines.extend(
        _section(
            "## 2. 開発の主目的",
            _build_core_purpose_lines(requirements),
        )
    )
    lines.extend(
        _section(
            "## 3. MVPの中心機能",
            _build_mvp_feature_group_lines(requirements),
        )
    )
    lines.extend(
        _section(
            "## 4. 主線フロー",
            _build_main_flow_lines(requirements),
        )
    )
    lines.extend(
        _section(
            "## 5. 技術方針",
            _build_bullet_lines(_as_string_list(requirements.get("technical_policy"))),
        )
    )
    lines.extend(
        _section(
            "## 6. 重要な設計方針",
            _build_bullet_lines(_as_string_list(requirements.get("design_principles"))),
        )
    )
    lines.extend(
        _section(
            "## 7. 制約条件",
            _build_bullet_lines(_as_string_list(requirements.get("constraints"))),
        )
    )
    lines.extend(
        _section(
            "## 8. 対象外（現時点）",
            _build_bullet_lines(_as_string_list(requirements.get("out_of_scope"))),
        )
    )
    lines.extend(
        _section(
            "## 9. 未確定事項・前提",
            _build_open_questions_lines(requirements),
        )
    )
    lines.extend(
        _section(
            "## 10. この文書の役割",
            [
                "この文書は、",
                "",
                "- planner の提案基準",
                "- plan_director の採択判断",
                "- task_router の優先順位判断",
                "",
                "の基準として使う。",
            ],
        )
    )

    return _join_doc_lines(lines)


def generate_completion_definition_doc(requirements: dict[str, Any]) -> str:
    """requirements.json から completion_definition.md を生成する."""

    lines: list[str] = [
        "# completion_definition",
        "",
        "## 目的",
        "",
        "本システムの「完成」を定義する。",
        "",
        "---",
        "",
        "## MVP 完成条件",
        "",
        "以下がすべて成立した状態を MVP 完成とする。",
        "",
        "---",
        "",
    ]

    completion_sections = _as_dict_list(requirements.get("mvp_completion_sections"))
    sorted_sections = sorted(
        completion_sections,
        key=lambda item: _completion_section_sort_key(item),
    )

    for index, section in enumerate(sorted_sections, start=1):
        section_name = _as_non_empty_string(section.get("section_name")) or f"セクション{index}"
        lines.append(f"## {index}. {section_name}")
        lines.append("")

        goal = _as_non_empty_string(section.get("goal"))
        if goal:
            lines.append(f"- 目的: {goal}")

        for item in _as_string_list(section.get("completion_items")):
            lines.append(f"- {item}")

        notes = _as_string_list(section.get("notes"))
        if notes:
            lines.append("")
            lines.append("補足:")
            for note in notes:
                lines.append(f"- {note}")

        judgement = _as_non_empty_string(section.get("judgement")) or "未判定"
        lines.append("")
        lines.append(f"> セクション判定: {judgement}")
        lines.append("")
        lines.append("---")
        lines.append("")

    lines.extend(
        _section(
            "## 5. 操作性",
            _build_bullet_lines(_as_string_list(requirements.get("operability_requirements"))),
            add_rule=True,
        )
    )
    lines.extend(
        _section(
            "## 6. 品質",
            _build_bullet_lines(_as_string_list(requirements.get("quality_requirements"))),
            add_rule=True,
        )
    )
    lines.extend(
        _section(
            "## 7. エラー処理・耐障害性",
            _build_bullet_lines(
                _as_string_list(requirements.get("error_handling_requirements"))
            ),
            add_rule=True,
        )
    )
    lines.extend(
        _section(
            "## 8. データ整合性",
            _build_bullet_lines(
                _as_string_list(requirements.get("data_integrity_requirements"))
            ),
            add_rule=True,
        )
    )
    lines.extend(
        _section(
            "## 9. 将来拡張（MVP後）",
            _build_future_extensions_lines(requirements),
        )
    )
    lines.extend(
        _section(
            "## 優先順位",
            _build_numbered_lines(_as_string_list(requirements.get("priority_order"))),
        )
    )
    lines.extend(
        _section(
            "## 対象外",
            _build_bullet_lines(_as_string_list(requirements.get("out_of_scope"))),
        )
    )

    return _join_doc_lines(lines)


def generate_feature_inventory_doc(requirements: dict[str, Any]) -> str:
    """requirements.json から feature_inventory.md を生成する."""

    lines: list[str] = [
        "# feature_inventory",
        "",
        "## 目的",
        "",
        "この文書は、repo 内の主要機能を棚卸しし、現在の状態を整理するための一覧である。  ",
        "planner / plan_director は、この文書を参照して以下を判断する。",
        "",
        "* 既実装か",
        "* 未接続か",
        "* 一部完了か",
        "* 未実装か",
        "* 対象外か",
        "* 重複 proposal になっていないか",
        "* 次にどの層を前進させるべきか",
        "",
        "---",
        "",
        "## 状態ラベル",
        "",
        "* `implemented`",
        "* `gui_unconnected`",
        "* `partial`",
        "* `not_implemented`",
        "* `gui_connected`",
        "* `out_of_scope`",
        "",
        "---",
        "",
        "## 記載ルール",
        "",
        "各機能は以下を必ず記載する。",
        "",
        "* 機能名",
        "* layer",
        "* status",
        "* summary",
        "* related_files",
        "* completion_links",
        "* task_split_notes",
        "* notes",
        "",
        "---",
        "",
        "## 機能一覧",
        "",
    ]

    features = _as_dict_list(requirements.get("feature_inventory"))
    sorted_features = sorted(features, key=lambda item: _feature_inventory_sort_key(item))

    for feature in sorted_features:
        feature_name = _as_non_empty_string(feature.get("feature_name")) or "[機能名]"
        lines.append(f"### {feature_name}")
        lines.append("")

        layers = _as_string_list(feature.get("layers"))
        status = _as_non_empty_string(feature.get("status")) or "not_implemented"
        summary = _as_non_empty_string(feature.get("summary"))
        completion_links = _as_string_list(feature.get("completion_links"))
        task_split_notes = _as_string_list(feature.get("task_split_notes"))
        related_files = _as_string_list(feature.get("related_files"))
        notes = _as_string_list(feature.get("notes"))

        layer_text = " / ".join(layers) if layers else "未記入"
        lines.append(f"* layer: {layer_text}")
        lines.append(f"* status: {status}")
        lines.append(f"* summary: {summary or '未記入'}")

        lines.append("")
        lines.append("* related_files:")
        if related_files:
            for file_path in related_files:
                lines.append(f"  * {file_path}")
        else:
            lines.append("  * 未記入")

        lines.append("")
        lines.append("* completion_links:")
        if completion_links:
            for link in completion_links:
                lines.append(f"  * {link}")
        else:
            lines.append("  * 未記入")

        lines.append("")
        lines.append("* task_split_notes:")
        if task_split_notes:
            for note in task_split_notes:
                lines.append(f"  * {note}")
        else:
            lines.append("  * 未記入")

        lines.append("")
        lines.append("* notes:")
        if notes:
            for note in notes:
                lines.append(f"  * {note}")
        else:
            lines.append("  * 未記入")

        lines.append("")
        lines.append("---")
        lines.append("")

    lines.extend(
        [
            "## planner / plan_director 用ルール",
            "",
            "### planner",
            "",
            "* `implemented` を未実装として提案しない",
            "* `gui_unconnected` は導線補完として扱う",
            "* `partial` は不足箇所を具体化する",
            "* `out_of_scope` は mainline で優先しない",
            "",
            "### plan_director",
            "",
            "* `implemented` は重複として減点",
            "* `gui_unconnected` は導線補完として評価",
            "* `partial` は completion_definition との接続で評価",
            "* `not_implemented` は完成条件への寄与で評価",
            "",
            "---",
            "",
            "## 更新ルール",
            "",
            "* task 完了後に更新する",
            "* 状態を曖昧にしない",
            "* completion_definition と整合させる",
            "* 重複機能を作らない",
            "",
        ]
    )

    return _join_doc_lines(lines)


def generate_requirements_docs(requirements: dict[str, Any]) -> dict[str, str]:
    """requirements.json から主要 docs を一括生成する."""

    return {
        ".claude_orchestrator/docs/project_core/開発の目的本筋.md": (
            generate_project_core_purpose_doc(requirements)
        ),
        ".claude_orchestrator/docs/completion_definition.md": (
            generate_completion_definition_doc(requirements)
        ),
        ".claude_orchestrator/docs/feature_inventory.md": (
            generate_feature_inventory_doc(requirements)
        ),
    }


def _build_project_overview_lines(requirements: dict[str, Any]) -> list[str]:
    product_summary = _as_non_empty_string(requirements.get("product_summary"))
    target_users = _as_string_list(requirements.get("target_users"))
    main_roles = _as_string_list(requirements.get("main_roles"))
    usage_modes = _as_string_list(requirements.get("usage_modes"))

    lines: list[str] = []
    if product_summary:
        lines.extend(
            [
                "本開発で作るものは、",
                f"**{product_summary}** である。",
                "",
            ]
        )
    else:
        lines.extend(
            [
                "本開発で作るものは、",
                "**未記入** である。",
                "",
            ]
        )

    lines.append("- 主対象:")
    if target_users:
        lines.extend([f"  - {item}" for item in target_users])
    else:
        lines.append("  - 未記入")

    lines.append("")
    lines.append("- 主な役割:")
    if main_roles:
        lines.extend([f"  - {item}" for item in main_roles])
    else:
        lines.append("  - 未記入")

    lines.append("")
    lines.append("- 利用形態:")
    if usage_modes:
        lines.extend([f"  - {item}" for item in usage_modes])
    else:
        lines.append("  - 未記入")

    return lines


def _build_core_purpose_lines(requirements: dict[str, Any]) -> list[str]:
    core_purpose = _as_non_empty_string(requirements.get("core_purpose"))
    value_points = _as_string_list(requirements.get("value_points"))

    lines: list[str] = []
    if core_purpose:
        lines.extend(
            [
                "本開発の目的は、",
                f"**{core_purpose}** を成立させることである。",
                "",
            ]
        )
    else:
        lines.extend(
            [
                "本開発の目的は、",
                "**未記入** を成立させることである。",
                "",
            ]
        )

    lines.append("特に以下を重視する。")
    lines.append("")
    if value_points:
        lines.extend([f"- {item}" for item in value_points])
    else:
        lines.append("- 未記入")

    return lines


def _build_mvp_feature_group_lines(requirements: dict[str, Any]) -> list[str]:
    groups = _as_dict_list(requirements.get("mvp_feature_groups"))

    lines: list[str] = ["以下を end-to-end で成立させる。", ""]
    if not groups:
        lines.append("### 未記入")
        lines.append("- 未記入")
        return lines

    for group in groups:
        name = _as_non_empty_string(group.get("name")) or "未記入"
        summary = _as_non_empty_string(group.get("summary"))
        group_requirements = _as_string_list(group.get("requirements"))

        lines.append(f"### {name}")
        lines.append(f"- 概要: {summary or '未記入'}")
        if group_requirements:
            for item in group_requirements:
                lines.append(f"- {item}")
        else:
            lines.append("- 未記入")
        lines.append("")

    if lines and lines[-1] == "":
        lines.pop()

    return lines


def _build_main_flow_lines(requirements: dict[str, Any]) -> list[str]:
    flow = _as_string_list(requirements.get("main_flow"))
    if not flow:
        return ["1. 未記入"]
    return _build_numbered_lines(flow)


def _build_open_questions_lines(requirements: dict[str, Any]) -> list[str]:
    open_questions = _as_string_list(requirements.get("open_questions"))
    if open_questions:
        return _build_bullet_lines(open_questions)
    return ["- 未記入"]


def _build_future_extensions_lines(requirements: dict[str, Any]) -> list[str]:
    extensions = _as_dict_list(requirements.get("future_extensions"))

    lines: list[str] = ["以下は拡張対象とするが、MVP完成条件には含めない。", ""]
    if not extensions:
        lines.append("### 未記入")
        lines.append("- 未記入")
        return lines

    for extension in extensions:
        category = _as_non_empty_string(extension.get("category")) or "未記入"
        items = _as_string_list(extension.get("items"))
        lines.append(f"### {category}")
        if items:
            for item in items:
                lines.append(f"- {item}")
        else:
            lines.append("- 未記入")
        lines.append("")

    if lines and lines[-1] == "":
        lines.pop()

    return lines


def _section(title: str, body_lines: list[str], *, add_rule: bool = False) -> list[str]:
    cleaned = _trim_blank_lines(body_lines)
    if not cleaned:
        cleaned = ["- 未記入"]

    lines: list[str] = [title, ""]
    lines.extend(cleaned)
    lines.append("")
    if add_rule:
        lines.append("> セクション判定: 未判定")
        lines.append("")
        lines.append("---")
        lines.append("")
    return lines


def _build_bullet_lines(items: list[str]) -> list[str]:
    if not items:
        return ["- 未記入"]
    return [f"- {item}" for item in items if item.strip()] or ["- 未記入"]


def _build_numbered_lines(items: list[str]) -> list[str]:
    if not items:
        return ["1. 未記入"]
    numbered = [
        f"{index}. {item}"
        for index, item in enumerate(items, start=1)
        if item.strip()
    ]
    return numbered or ["1. 未記入"]


def _completion_section_sort_key(section: dict[str, Any]) -> tuple[int, str]:
    priority = section.get("priority")
    if not isinstance(priority, int):
        priority = 9999
    name = _as_non_empty_string(section.get("section_name"))
    return (priority, name)


def _feature_inventory_sort_key(feature: dict[str, Any]) -> tuple[int, str]:
    status_priority = {
        "partial": 0,
        "not_implemented": 1,
        "gui_unconnected": 2,
        "implemented": 3,
        "gui_connected": 4,
        "out_of_scope": 5,
    }
    status = _as_non_empty_string(feature.get("status"))
    name = _as_non_empty_string(feature.get("feature_name"))
    return (status_priority.get(status, 9999), name)


def _trim_blank_lines(lines: list[str]) -> list[str]:
    trimmed = lines[:]
    while trimmed and not trimmed[0].strip():
        trimmed.pop(0)
    while trimmed and not trimmed[-1].strip():
        trimmed.pop()
    return trimmed


def _join_doc_lines(lines: list[str]) -> str:
    normalized: list[str] = []
    last_blank = False

    for line in lines:
        current = line.rstrip()
        if not current:
            if last_blank:
                continue
            normalized.append("")
            last_blank = True
            continue
        normalized.append(current)
        last_blank = False

    while normalized and normalized[-1] == "":
        normalized.pop()

    return "\n".join(normalized) + "\n"


def _as_string_list(value: Any) -> list[str]:
    if not isinstance(value, list):
        return []

    result: list[str] = []
    for item in value:
        if not isinstance(item, str):
            continue
        normalized = item.strip()
        if not normalized:
            continue
        result.append(normalized)
    return result


def _as_dict_list(value: Any) -> list[dict[str, Any]]:
    if not isinstance(value, list):
        return []

    result: list[dict[str, Any]] = []
    for item in value:
        if isinstance(item, dict):
            result.append(item)
    return result


def _as_non_empty_string(value: Any) -> str:
    if not isinstance(value, str):
        return ""
    return value.strip()
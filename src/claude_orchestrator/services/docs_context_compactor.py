# src/claude_orchestrator/services/docs_context_compactor.py
from __future__ import annotations

from pathlib import PurePosixPath
import re


_FEATURE_RULE_HEADINGS = {
    "目的",
    "状態ラベル",
    "planner / plan_director 用ルール",
    "更新ルール",
}

_TASK_HISTORY_RULE_HEADINGS = {
    "目的",
}


def compact_core_doc_text(relative_path: str, content: str) -> str:
    normalized = str(relative_path).replace("\\", "/").strip()
    name = PurePosixPath(normalized).name

    if name == "feature_inventory.md":
        return compact_feature_inventory_text(content)

    if name == "過去TASK作業記録.md":
        return compact_task_history_text(content)

    return content


def compact_feature_inventory_text(content: str, *, max_feature_entries: int = 12) -> str:
    if not content.strip():
        return content

    lines = content.splitlines()
    sections = _split_markdown_sections(lines)

    doc_title = _extract_first_heading(lines) or "# feature_inventory"

    out: list[str] = [doc_title, ""]

    # ルール系セクションを先に compact 化して残す
    for section in sections:
        heading_text = section["heading_text"]
        if heading_text in _FEATURE_RULE_HEADINGS:
            body_lines = _clean_section_body(section["body_lines"])
            if not body_lines:
                continue
            out.append(section["heading_line"])
            out.extend(body_lines)
            out.append("")

    # 実機能一覧を compact 化
    feature_entries = _extract_feature_inventory_entries(sections)
    if feature_entries:
        out.append("## compact feature entries")
        for entry in feature_entries[:max_feature_entries]:
            out.append(
                f"- feature: {entry['title']} | status: {entry['status']} | "
                f"layer: {entry['layer']} | related_files: {entry['related_files']}"
            )
            if entry["notes"]:
                out.append(f"  notes: {entry['notes']}")
        if len(feature_entries) > max_feature_entries:
            out.append(
                f"- remaining_entries: {len(feature_entries) - max_feature_entries}"
            )
        out.append("")

    compact_text = "\n".join(out).strip()
    return compact_text if compact_text else content


def compact_task_history_text(content: str, *, max_blocks: int = 8) -> str:
    if not content.strip():
        return content

    lines = content.splitlines()
    sections = _split_markdown_sections(lines)
    doc_title = _extract_first_heading(lines) or "# 過去TASK作業記録"

    out: list[str] = [doc_title, ""]

    # 目的などの先頭ルールは残す
    for section in sections:
        heading_text = section["heading_text"]
        if heading_text in _TASK_HISTORY_RULE_HEADINGS:
            body_lines = _clean_section_body(section["body_lines"])
            if not body_lines:
                continue
            out.append(section["heading_line"])
            out.extend(body_lines)
            out.append("")

    # 履歴本体は後ろ側の最近ブロックだけ残す
    content_sections = [
        section
        for section in sections
        if section["heading_text"] not in _TASK_HISTORY_RULE_HEADINGS
    ]
    tail_sections = content_sections[-max_blocks:]

    if tail_sections:
        out.append("## recent extracted history")
        out.append("")
        for section in tail_sections:
            out.append(section["heading_line"])
            body_lines = _clean_section_body(section["body_lines"])
            if body_lines:
                out.extend(body_lines)
            out.append("")

    compact_text = "\n".join(out).strip()
    return compact_text if compact_text else content


def _split_markdown_sections(lines: list[str]) -> list[dict[str, object]]:
    sections: list[dict[str, object]] = []
    current_heading_line: str | None = None
    current_heading_text: str | None = None
    current_body: list[str] = []

    for line in lines:
        if _is_heading(line):
            if current_heading_line is not None:
                sections.append(
                    {
                        "heading_line": current_heading_line,
                        "heading_text": current_heading_text or "",
                        "body_lines": current_body[:],
                    }
                )
            current_heading_line = line
            current_heading_text = _normalize_heading_text(line)
            current_body = []
            continue

        if current_heading_line is not None:
            current_body.append(line)

    if current_heading_line is not None:
        sections.append(
            {
                "heading_line": current_heading_line,
                "heading_text": current_heading_text or "",
                "body_lines": current_body[:],
            }
        )

    return sections


def _extract_feature_inventory_entries(
    sections: list[dict[str, object]],
) -> list[dict[str, str]]:
    entries: list[dict[str, str]] = []

    for section in sections:
        heading_line = str(section["heading_line"])
        heading_text = str(section["heading_text"])
        body_lines = [str(x) for x in section["body_lines"]]

        if not heading_line.startswith("### "):
            continue
        if heading_text in _FEATURE_RULE_HEADINGS:
            continue

        layer = ""
        status = ""
        notes_parts: list[str] = []
        related_files: list[str] = []

        capture_related = False
        for raw in body_lines:
            line = raw.strip()
            if not line:
                capture_related = False
                continue

            if line.startswith("- layer:"):
                layer = line.removeprefix("- layer:").strip()
                capture_related = False
                continue

            if line.startswith("- status:"):
                status = line.removeprefix("- status:").strip()
                capture_related = False
                continue

            if line.startswith("- related_files:"):
                capture_related = True
                value = line.removeprefix("- related_files:").strip()
                if value and value != "[]":
                    related_files.append(value)
                continue

            if line.startswith("- notes:"):
                value = line.removeprefix("- notes:").strip()
                if value:
                    notes_parts.append(value)
                capture_related = False
                continue

            if capture_related and line.startswith("- "):
                related_files.append(line.removeprefix("- ").strip())
                continue

            if line.startswith("- "):
                notes_parts.append(line.removeprefix("- ").strip())
                capture_related = False
                continue

        entries.append(
            {
                "title": heading_text,
                "layer": layer or "unknown",
                "status": status or "unknown",
                "related_files": ", ".join(related_files[:4]) if related_files else "[]",
                "notes": " / ".join(notes_parts[:2]),
            }
        )

    return entries


def _extract_first_heading(lines: list[str]) -> str:
    for line in lines:
        if line.startswith("# "):
            return line
    return ""


def _clean_section_body(body_lines: list[object]) -> list[str]:
    cleaned: list[str] = []
    last_blank = False

    for value in body_lines:
        line = str(value).rstrip()
        if not line:
            if last_blank:
                continue
            cleaned.append("")
            last_blank = True
            continue
        cleaned.append(line)
        last_blank = False

    while cleaned and cleaned[-1] == "":
        cleaned.pop()

    return cleaned


def _is_heading(line: str) -> bool:
    return bool(re.match(r"^#{1,6}\s+", line))


def _normalize_heading_text(line: str) -> str:
    return re.sub(r"^#{1,6}\s+", "", line).strip()
# src\claude_orchestrator\gui\services\requirements_prompt_service.py
from __future__ import annotations

import json
from pathlib import Path

from claude_orchestrator.services.requirements_context_compactor import (
    build_requirements_context,
)


def build_requirements_authoring_prompt(
    *,
    repo_path: str,
    requirements_json: dict,
    user_request: str,
    schema_text: str,
) -> str:
    repo_root = Path(repo_path).resolve()
    compact_context = build_requirements_context(
        requirements_json,
        mode="requirements_authoring",
        max_feature_groups=8,
    )
    current_requirements_json_text = json.dumps(
        requirements_json,
        ensure_ascii=False,
        indent=2,
    )

    normalized_request = (
        user_request.strip() or "現在の requirements.json を改善してください。"
    )

    return f"""あなたは requirements 定義補助専用アシスタントです。

対象 repo:
{repo_root}

目的:
- ユーザーの要望をもとに requirements.json を改善する
- 既存の requirements.json をベースに、必要な補完・整理・改善を行う
- 不確かな内容は勝手に断定せず、必要なら open_questions に残す
- 既存の情報を無断で大量削除しない
- ユーザーの意図に関係ない項目は変更しない

最重要ルール:
- 出力は requirements.schema.json に適合する JSON オブジェクトのみ
- Markdown を使わない
- 説明文を前後に付けない
- ``` や ```json のようなコードフェンスを使わない
- JSON 以外を一切出力しない
- root は object であること
- 必須項目を欠落させないこと
- 既存の _meta.relative_path は維持すること
- 不足情報は open_questions や notes に寄せること
- requirements の意味を崩さないこと

厳格出力ルール:
- 出力の先頭1文字は必ず {{ にすること
- 出力の末尾は必ず }} で終えること
- 空行を含めて JSON 以外の文字を一切含めないこと
- 「以下がJSONです」「修正版です」などの文を絶対に付けないこと
- コードブロック記号 ``` を絶対に出力しないこと
- もし迷っても JSON だけを返すこと

ユーザーからの今回の依頼:
{normalized_request}

現在の requirements compact context:
{compact_context}

現在の requirements.json 全文:
{current_requirements_json_text}

requirements.schema.json:
{schema_text}

このルールに従い、更新後の requirements.json 全文だけを返してください。
"""
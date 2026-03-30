# src\claude_orchestrator\gui\services\refine_requirements_prompt_service.py
from __future__ import annotations

import json


def build_refine_requirements_prompt(
    *,
    repo_path: str,
    requirements_json: dict,
    review_json: dict,
    schema_text: str,
) -> str:
    requirements_text = json.dumps(requirements_json, indent=2, ensure_ascii=False)
    review_text = json.dumps(review_json, indent=2, ensure_ascii=False)

    return f"""あなたは要件改善エンジニアです。

以下のレビュー結果に基づき、
requirements.json を修正してください。

制約:
- 出力は requirements.json のみ（JSON）
- schema に必ず準拠する
- 構造を壊さない
- 意味を劣化させない
- 不明点は assumptions または open_questions に移動する

修正ルール:
- critical は必ず解消する
- major は可能な限り解消する
- schema違反は必ず修正する
- 過剰な機能は削る
- 矛盾は統一する
- review の指摘を解消するために requirements の本来の意図を壊さない
- 不確定要素を勝手に断定しない

最重要出力ルール:
- 出力は JSON オブジェクトのみ
- JSON 以外の文字を1文字でも出力してはいけない
- Markdown を使わない
- 説明文を前後に付けない
- 修正概要、要約、補足、コメントを書かない
- 「requirements.json を修正しました」「対応した指摘」などの文を絶対に出力しない
- ``` や ```json のようなコードフェンスを使わない
- 出力の先頭1文字は必ず {{ にすること
- 出力の末尾は必ず }} で終えること
- 空行を含めて JSON 以外の文字を一切含めないこと
- あなたの出力はそのまま json.loads() に渡される
- JSON 以外を1文字でも出力すると処理は即失敗する
- 修正内容の説明は不要であり、出力してはならない
- 出力は「修正済み requirements.json 全文」そのものだけである

出力例:
{{
  "_meta": {{
    "relative_path": "..."
  }},
  "project_name": "...",
  "requirement_status": "...",
  "...": "..."
}}

出力スキーマ:
{schema_text}

元requirements.json:
{requirements_text}

レビュー結果:
{review_text}

修正済み requirements.json 全文だけを返してください。
"""
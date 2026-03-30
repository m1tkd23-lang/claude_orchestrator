# src/claude_orchestrator/gui/services/review_requirements_prompt_service.py
from __future__ import annotations

import json
from pathlib import Path


def build_review_requirements_prompt(
    *,
    repo_path: str,
    requirements_json: dict,
    schema_text: str,
) -> str:
    repo_root = Path(repo_path).resolve()
    requirements_text = json.dumps(requirements_json, indent=2, ensure_ascii=False)

    return f"""あなたは要件定義レビュー担当です。

対象 repo:
{repo_root}

以下の requirements.json を厳密にレビューしてください。

制約:
- 出力は必ず JSON のみ
- スキーマに完全準拠すること
- 曖昧な表現は禁止
- 問題がなければ issues は空配列にする
- strengths は必ず記載する
- consistency_checks は必ず全項目を埋める
- recommended_actions は必ず記載する

レビュー観点:
1. 目的整合性
2. スコープ適正
3. フロー整合性
4. 完成条件整合性
5. 制約整合性
6. 未確定明示
7. task分割可能性

禁止事項:
- 未確定を確定として扱う
- constraints を無視する
- out_of_scope を主線に戻す
- schema違反を見逃す
- flow / feature / completion の不整合を放置する
- JSON以外の文字を出力する

最重要出力ルール:
- 出力は JSON オブジェクトのみ
- Markdown を使わない
- 説明文を前後に付けない
- ``` や ```json のようなコードフェンスを使わない
- JSON 以外を一切出力しない
- 出力の先頭1文字は必ず {{ にすること
- 出力の末尾は必ず }} で終えること
- 空行を含めて JSON 以外の文字を一切含めないこと
- 「レビュー結果です」「以下にJSONを返します」などの文を絶対に付けないこと
- もし迷っても JSON だけを返すこと

出力スキーマ:
{schema_text}

対象 requirements.json:
{requirements_text}

レビュー結果 JSON 全文だけを返してください。
"""
# src\claude_orchestrator\gui\services\remote_prompt_service.py
from __future__ import annotations

from pathlib import Path


DEFAULT_PROMPT_TEMPLATE = """あなたは claude_orchestrator の Remote Operator として振る舞ってください。

対象 repo:
{repo_path}

目的:
- ユーザーの数字入力に応じて remote operator 用 CLI を実行する
- CLI の標準出力をそのまま返し、次の数字入力待ち状態を維持する

基本ルール:
- 毎回ローカル repo 上で CLI を実行する
- 会話開始時、メニュー再表示要求時、数字以外の入力時は remote-menu を実行する
- ユーザー入力が数字のみの場合は remote-select を実行する
- CLI の標準出力は一切加工せず、そのまま返す
- 要約しない
- 補足説明を足さない
- 行を削らない
- 行順を変えない
- 番号表示を書き換えない
- [0] 戻る や [1] などの表記を別の番号へ変換しない
- コマンド自体は表示しない

長い処理について:
- CLI 実行中は待機する
- 処理途中で独自メッセージを出さない
- 処理完了後は、CLI の最終出力をそのまま返す
- 返答は必ず次の数字入力ができるメニュー表示状態で終わるものとする

実行コマンド:
- メニュー表示
python -m claude_orchestrator.cli.main remote-menu --repo "{repo_path}"

- 数字入力処理
python -m claude_orchestrator.cli.main remote-select --repo "{repo_path}" --input "<number>"

開始手順:
まず最初に remote-menu を実行し、その標準出力をそのまま表示してください。
"""


def _get_packaged_prompt_template_path() -> Path:
    return (
        Path(__file__).resolve().parents[2]
        / "template_assets"
        / "project_bundle"
        / ".claude_orchestrator"
        / "prompts"
        / "remote_operator.txt"
    )


def load_remote_prompt(repo_path: str) -> str:
    repo = Path(repo_path).resolve()

    repo_prompt_file = (
        repo
        / ".claude_orchestrator"
        / "prompts"
        / "remote_operator.txt"
    )

    packaged_prompt_file = _get_packaged_prompt_template_path()

    if repo_prompt_file.exists():
        text = repo_prompt_file.read_text(encoding="utf-8", errors="replace")
    elif packaged_prompt_file.exists():
        text = packaged_prompt_file.read_text(encoding="utf-8", errors="replace")
    else:
        text = DEFAULT_PROMPT_TEMPLATE

    return text.replace("{repo_path}", str(repo))
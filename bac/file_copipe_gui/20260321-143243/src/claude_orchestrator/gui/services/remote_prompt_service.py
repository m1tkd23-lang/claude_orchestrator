# src\claude_orchestrator\gui\services\remote_prompt_service.py
from __future__ import annotations

from pathlib import Path


DEFAULT_PROMPT_TEMPLATE = """あなたは claude_orchestrator の Remote Operator として振る舞ってください。

対象 repo:
{repo_path}

基本ルール:
- 毎回ローカル repo 上で CLI を実行して結果だけを返す
- 数字のみの入力を受けたら remote-select を実行する
- 会話開始時、またはメニュー表示要求のときは remote-menu を実行する
- 不要な説明は足さない
- 結果は CLI の標準出力をそのまま返す

実行コマンド:
- メニュー表示
python -m claude_orchestrator.cli.main remote-menu --repo "{repo_path}"

- 数字入力処理
python -m claude_orchestrator.cli.main remote-select --repo "{repo_path}" --input "<number>"

まず最初に remote-menu を実行して結果を表示してください。
"""


def load_remote_prompt(repo_path: str) -> str:
    repo = Path(repo_path).resolve()

    prompt_file = (
        repo
        / ".claude_orchestrator"
        / "prompts"
        / "remote_operator.txt"
    )

    if prompt_file.exists():
        text = prompt_file.read_text(encoding="utf-8", errors="replace")
    else:
        text = DEFAULT_PROMPT_TEMPLATE

    return text.replace("{repo_path}", str(repo))
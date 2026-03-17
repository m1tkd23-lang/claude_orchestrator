# README.md
# claude_orchestrator

複数役割の Claude エージェントを親オーケストレータが制御し、
実装・レビュー・承認の流れを管理するためのリポジトリです。

## 初期対象
- drawing_review_app

## 初期MVPの範囲
- implementer
- reviewer
- approver
- report 出力
- target repo 切替設定

## セットアップ

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -U pip
pip install -e .
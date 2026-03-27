<!-- README_dist_template.md -->
# Claude Orchestrator EXE版 使い方

## 1. 配布物
配布フォルダ内の主なファイルは以下です。

- `claude_orchestrator.exe`
- `README.md`

※ 実際には実行に必要な依存ファイルも同じフォルダ内に含まれます。  
※ フォルダごと保持してください。

## 2. 起動方法
`claude_orchestrator.exe` を起動してください。

## 3. 事前に必要なもの
このアプリは Claude Code CLI を外部コマンドとして利用します。  
そのため、利用PCには以下が必要です。

- Node.js インストール済み
- Claude Code CLI インストール済み
- `claude` コマンドが PATH に通っている
- Claude へログイン済み

確認コマンド:

```powershell
node -v
npm -v
claude --version
claude -p "hello"
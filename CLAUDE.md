<!-- CLAUDE.md -->
このリポジトリは claude_orchestrator によりタスク駆動で更新される。

- task.json / state.json を最優先の根拠とする
- role の責務を越えない（実装・評価・判断を混ぜない）
- 指定された context_files のみを参照する
- 推測で不足情報を補わない
- 無関係なファイル変更を行わない
- 出力は必ず指定 schema の JSON のみ
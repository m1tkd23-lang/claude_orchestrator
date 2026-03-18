# src\claude_orchestrator\template_assets\project_bundle\.claude_orchestrator\skills\reviewer\code-review.md
# code-review

reviewer 用 skill です。

## 目的

implementer の作業結果を、安全性と整合性の観点から確認すること。

## 観点

1. task の目的に沿っているか
2. 指示範囲を広げすぎていないか
3. changed_files と summary が整合しているか
4. リスクや未解決点が十分に書かれているか
5. 既存構造を壊す危険がないか
6. 追加確認が必要な点は must_fix / nice_to_have に整理する

## 出力方針

- 重大な問題は must_fix に入れる
- 改善提案レベルは nice_to_have に入れる
- 問題がなければ ok
- 危険で進められない場合は blocked
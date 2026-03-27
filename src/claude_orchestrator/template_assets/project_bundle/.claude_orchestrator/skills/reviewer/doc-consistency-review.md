# doc-consistency-review

reviewer 用 skill です。docs / research タスクに特化しています。

## 目的

docs / research タスクの implementer 成果物を、記述品質と整合性の観点から確認すること。

## 観点

1. 記述の一貫性: 同一概念・用語が文書内で統一されているか
2. 前提の矛盾: 他の記述や既存ドキュメントと矛盾する前提が含まれていないか
3. 曖昧表現: 解釈が複数生まれる表現、主語不明、条件不明の記述がないか
4. 既存ルールとの整合性: workflow_rules.md など既存ルール文書と食い違う内容がないか

## 出力方針

- 重大な問題は must_fix に入れる
- 改善提案レベルは nice_to_have に入れる
- 問題がなければ ok
- 判断不能な場合は blocked

## code-review との違い

- code-review は実装の安全性・構造破壊リスク・changed_files 整合を主眼とする
- doc-consistency-review は文書の記述品質・論理整合・既存ルールとの一致を主眼とする
- 実装ファイル（.py / .ts など）の変更には code-review を使うこと

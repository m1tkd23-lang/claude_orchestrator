<!-- CLAUDE.md -->

このリポジトリは claude_orchestrator によりタスク駆動で更新される。

## 最優先ルール

* task.json / state.json を唯一の実行根拠とする

- 以下のファイルを参照して判断する
  - .claude_orchestrator/docs/completion_definition.md
  - .claude_orchestrator/docs/feature_inventory.md


* role の責務を越えない（実装・評価・判断を混ぜない）

## 実装ルール

* 指定された context_files のみを参照する
* 推測で不足情報を補わない
* 無関係なファイル変更を行わない
* 既存コードを破壊する変更を行わない

## 設計方針

* MVP最小構成を優先する（過剰実装を禁止）
* 小さく確実に完了する実装を行う
* 後から変更できる構造（拡張可能・分離）を維持する

## 実行環境

* Python仮想環境（.venv）上で動作する前提とする
* 環境依存の差異が出ない構成を優先する

## 出力ルール

* 出力は必ず指定 schema の JSON のみ

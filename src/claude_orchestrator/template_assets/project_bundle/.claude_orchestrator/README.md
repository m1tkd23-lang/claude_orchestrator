# src\claude_orchestrator\template_assets\project_bundle\.claude_orchestrator\README.md
# .claude_orchestrator

このフォルダは、対象リポジトリ上で claude_orchestrator による
半自動オーケストレーション運用を行うための管理フォルダです。

## 役割

- roles/
  - Claude Code 各役割の定義
- schemas/
  - JSON 入出力の検証用 schema
- templates/
  - 各役割へ渡す prompt テンプレート
- config/
  - 対象 repo ごとの差分設定
- tasks/
  - 個別タスクの管理データ
- runtime/
  - 一時ファイル、ログ、運用時生成物

## 基本運用

1. 親アプリが task を作成する
2. 親アプリが next role 用の prompt を生成する
3. 人が Claude Code に prompt を貼り付ける
4. Claude Code が JSON report を出力する
5. 親アプリが report を検証する
6. 親アプリが次 role を決定する

## 重要ルール

- Claude Code は毎回新規セッションで使用する
- Claude の出力は JSON のみとする
- state 更新は Python 側が行う
- Claude は role 定義と schema に従う
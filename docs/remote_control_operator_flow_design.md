# docs\remote_control_operator_flow_design.md

# Remote Control Operator Flow 設計書 v1

## 1. 目的

本設計は、claude_orchestrator において

- ローカルGUI運用
- Claude Code Remote Control（スマホ操作）

を両立させ、

**スマホから番号選択のみでタスクを進行できる運用フロー**

を構築することを目的とする。

---

## 2. スコープ

本設計で対象とする範囲：

- GUI → Remote Control 起動導線
- Remote Claude セッションの運用ルール
- 番号選択型オペレーション仕様
- CLI / UseCase との接続

対象外：

- Web UI（別フェーズ）
- 複数ユーザー同時制御
- 認証強化（v2以降）

---

## 3. 全体構成


[GUI]
├─ repo選択
├─ task操作（従来通り）
└─ Remote Control起動
↓
[Claude Code Remote Control]
↓
[スマホ / claude.ai/code]
↓
[Remote Operator Session]
↓
[claude_orchestrator CLI / UseCase]
↓
[.claude_orchestrator データ]


---

## 4. コンポーネント責務

### 4.1 GUI

役割：

- repo選択
- ローカル操作
- Remote Control 起動補助

責務：

- `claude remote-control` の起動
- URL表示
- QR表示（任意）

非責務：

- Remote操作ロジック
- 番号分岐処理

---

### 4.2 Remote Control セッション

役割：

- スマホ操作の受け口
- オペレーター対話制御

責務：

- メニュー提示
- 番号入力の解釈
- CLI実行
- 結果整形

---

### 4.3 CLI / UseCase

役割：

- 実処理

使用コマンド：

- status
- generate-next-tasks
- list-proposals
- create-task-from-proposal
- run-task

---

## 5. Remote Control 起動仕様

### 5.1 起動コマンド

```bash
claude remote-control
5.2 モード
spawn mode: same-dir

理由：

orchestratorは同一ディレクトリ共有前提

state.json / task.json を共有するため

6. Remote Operator セッション仕様
6.1 基本ルール

出力は常に番号付き

入力は「番号のみ」を想定

不正入力は再提示

常に次アクションを提示

6.2 メインメニュー

例：

現在の操作候補です

1. in_progress task を実行
2. completed task から次タスク案を作成
3. task 一覧を表示
4. 特定 task を選択
5. 終了

番号で入力してください
6.3 タスク実行フロー
1選択時

処理：

status → in_progress抽出
→ 対象task選択
→ run-task実行

実行後：

タスク実行が完了しました

1. 次タスク案を作成する
2. task一覧へ戻る
6.4 plannerフロー
completed task選択
generate-next-tasks
list-proposals

出力：

TASK-0010 の次タスク案

1. PLAN-0001
2. PLAN-0002
3. 戻る
6.5 proposal → task化
PLAN選択時
create-task-from-proposal

出力：

TASK-0015 を作成しました

1. そのまま実行
2. 戻る
6.6 task実行
run-task

出力：

TASK-0015 実行完了

1. 次タスク案作成
2. メニューへ戻る
7. 状態管理

Remoteセッションはステートレスに近いが、

以下は保持する：

現在選択中 task_id

現在選択中 proposal_id

8. エラーハンドリング
8.1 不正入力
無効な入力です
番号で入力してください
8.2 CLI失敗
処理に失敗しました
ログを確認してください

1. 再試行
2. メニューへ戻る
9. 運用ルール
9.1 同時操作禁止

GUI と Remote の同時操作禁止

同一 task の並行実行禁止

9.2 セッション管理

remote-control セッションは1つ推奨

終了時は /remote-control で切断

9.3 ログ確認

logsディレクトリで確認

10. 将来拡張

自動ループ実行（完全自律）

Web UI統合

通知（Slack / LINE）

音声操作

AI自動判断分岐

11. 実装ステップ
Step1

Remote Operator Prompt 作成

Step2

GUIに Remote起動ボタン追加（任意）

Step3

CLI呼び出し統合

Step4

番号分岐ロジック実装

12. まとめ

本設計により、

GUI → ローカル操作

Remote → スマホ操作

を分離しつつ、

番号入力のみでタスクを回す運用

が実現できる。
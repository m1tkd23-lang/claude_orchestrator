<!-- docs\Claude Orchestrator GUI 開発記録 & 次工程指示書.md -->
# Claude Orchestrator GUI 開発記録 & 次工程指示書

## 1. ここまでの作業まとめ

### 1.1 GUI MVP の実装

PySide6 を用いて Claude Orchestrator の GUI を構築した。

実装済み機能:

- repo パス指定
- `.claude_orchestrator` 初期化確認
- init-project 実行
- task 一覧表示
- task 詳細表示
- task 作成
- show-next
- prompt 表示
- output json path 表示
- validate-report
- advance
- ログ表示

---

### 1.2 repo 切替時の状態バグ修正

問題:
- repo 切替後も前の task 情報が残る

対応:
- repo変更時に以下をクリア
  - task一覧
  - task詳細
  - prompt表示
  - validation表示
  - 実行モニタ表示
- 一覧再読込時に存在しない task はクリア

---

### 1.3 prompt template 改修（保存実行前提）

Claude に JSON を返させるだけでなく、  
**指定パスに保存させる構成へ変更**

追加内容:

- 作業対象 repo 明示
- JSON 保存先（絶対パス / 相対パス）
- 保存義務の明示
- 誤った repo への保存禁止

対象:

- implementer_prompt.txt
- reviewer_prompt.txt
- director_prompt.txt

---

### 1.4 ShowNextUseCase 修正

追加対応:

- `{target_repo}`
- `{task_id}`
- `{cycle}`

を prompt に埋め込むよう修正

---

### 1.5 revise / approve フロー確認

sandbox_repo にて確認済み:

- implementer → reviewer → director → completed
- director revise → implementer (cycle+1)
- cycle 管理
- validate / advance の整合性

---

### 1.6 実repoでの Claude Code 連携検証

対象:

`D:\Develop\claude_test_repo`

確認内容:

- GUI → prompt生成
- Claudeへ貼り付け実行
- README.md 更新
- report JSON 保存
- GUI validate
- GUI advance

結果:

**フルワークフロー成立**

---

### 1.7 非対話実行（claude -p）の検証

以下コマンドで成功:

```powershell
Get-Content .claude_orchestrator\tasks\TASK-0002\outbox\implementer_prompt_v1.txt -Raw | claude -p --permission-mode bypassPermissions

確認事項:

非対話実行可能

permission確認回避可能

JSON保存成功

ファイル編集成功

結論:

subprocess による自動実行が可能

1.8 GUIコード分割

分割構成:

gui/
├── main_window.py
├── ui_sections.py
├── state_helpers.py
├── dialog_helpers.py
└── claude_runner.py

結果:

全機能正常動作

可読性向上

拡張しやすい構造へ改善

1.9 Claude 非対話実行の GUI 統合

実装内容:

Claude実行(1ステップ) ボタン追加

GUI から claude -p --permission-mode bypassPermissions 実行

prompt を Python から標準入力で渡す構成

JSON 保存確認

implementer / reviewer / director での動作確認

確認結果:

GUI → Claude CLI 実行成功

report JSON 保存成功

validate-report 成功

advance 成功

1.10 自動完了までのループ実行追加

実装内容:

Claude実行(自動完了まで) ボタン追加

show-next → Claude実行 → JSON保存確認 → validate → advance を自動ループ

completed 到達で自動停止

revise 時は implementer に戻って継続可能

確認結果:

TASK-0004 にて 1 クリックで completed まで到達

implementer / reviewer / director を自動で通過

README.md 更新、3種 report JSON 生成、state 遷移が正常動作

1.11 QThread による非同期実行対応

実装内容:

自動実行処理を QThread + Worker に分離

GUI メインスレッドをブロックしない構成へ変更

signal により進行状況・ログ・validation 結果を UI に反映

確認結果:

実行中に GUI が固まらない

タブ切替や表示確認が可能

自動完了までの処理が非同期で正常動作

1.12 タブ構成と Claude 実行モニタ追加

構成変更:

タブ1: 実行

repo

新規 task 作成

task 一覧

選択 task の現在ステータス

Claude実行(自動完了まで) ボタン

実行状態表示

Claude実行モニタ

結果ログ

タブ2: 詳細

task 詳細

prompt 表示

output json path

validation 結果

手動操作

再読込

追加内容:

Claude実行モニタ

process started

role / cycle

cwd

stdout

stderr

report file detected

validate success

advanced to next role

completed

確認結果:

実行中の状態が追跡しやすくなった

接続できているか、動いているか、どこまで進んだかが可視化された

TASK-0005 にて completed までのモニタ表示を確認済み

2. 現在の到達点

以下が成立している:

ワークフロー

implementer

reviewer

director

revise

completed

システム連携

GUI → prompt生成

Claude → repo編集

Claude → JSON保存

GUI → validate

GUI → advance

GUI → completed まで自動ループ

GUI → 非同期実行

GUI → 実行モニタ表示

実運用に近い確認

実repo に対して 1クリックで completed まで進行可能

実行中でも GUI が応答する

進行状況が画面上で確認できる

3. 現在の課題
3.1 実行モニタ文言の重複整理

現状でも実用上は問題ないが、以下のような重複がある。

advanced to next role の近い内容が複数出る場合がある

process started の文言整理余地がある

3.2 一覧更新時の task detail loaded ログが多い

一覧更新と再選択で task detail loaded が複数回出る。
機能上の問題はないが、ログ可読性改善余地あり。

3.3 completed 後の UX 改善余地

completed task に対する操作の見せ方や制御は改善余地がある。

3.4 planner 機能未着手

completed 後の次 task 提案を AI に補助させる planner 機能は、まだ未実装。

4. 次の実装指示書
4.1 作業名

planner v1 の追加

4.2 目的

completed task をもとに、AI に次の実装 task 候補を提案させる。

4.3 実装する

planner ロール追加

planner prompt / schema 追加

「次タスク案作成」ボタン追加

planner report JSON 生成

候補一覧表示

採用 / 否決 / 保留

採用時の task 作成欄への転記

4.4 実装しない

planner の自動起動

planner 候補の自動採用

planner 候補からの task 自動作成

実 task の物理削除

repo 全体の無制限読込

4.5 実装方針

planner は completed task を入力とする

source task の task/state/report と、指定 docs を入力に含める

出力は 1〜3 件の task 候補 JSON

候補は task 化しやすい粒度で出す

最終判断は人が行う

4.6 対象ファイル案

新規:

src\claude_orchestrator\application\usecases\generate_next_task_proposals_usecase.py

src\claude_orchestrator\gui\planner_helpers.py

src\claude_orchestrator\gui\proposal_state_store.py

src\claude_orchestrator\template_assets\project_bundle\.claude_orchestrator\roles\planner.md

src\claude_orchestrator\template_assets\project_bundle\.claude_orchestrator\templates\planner_prompt.txt

src\claude_orchestrator\template_assets\project_bundle\.claude_orchestrator\schemas\planner_report.schema.json

更新:

src\claude_orchestrator\gui\ui_sections.py

src\claude_orchestrator\gui\main_window.py

5. まとめ

現在の状態は

「AIを GUI から非同期で自動実行し、完了まで監視できるオーケストレーター」

である。

次の段階は

「完了後に次の task 候補まで提案できるオーケストレーター」

への進化である。
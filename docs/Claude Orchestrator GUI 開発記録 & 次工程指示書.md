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


D:\Develop\claude_test_repo


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
└── dialog_helpers.py

結果:

全機能正常動作

可読性向上

拡張しやすい構造へ改善

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

3. 現在の課題
3.1 人手操作が残っている

現在:

GUI → promptコピー → Claude貼り付け → 実行

これを自動化したい。

3.2 completed後のUX

validate-report がエラーになる（仕様上正しいがUX改善余地あり）

3.3 Claude実行のGUI未統合

claude -p は検証済み

GUIから呼べていない

4. 次の実装指示書
4.1 作業名

Claude 非対話実行の GUI 統合（1ステップ実行）

4.2 目的

Claude実行をGUIに統合し、以下を1クリックで実行可能にする:

show-next
→ claude 実行
→ JSON保存
→ validate
→ advance
4.3 実装対象
実装する

Claude実行ボタン

subprocess 実行

JSON存在確認

validate 自動実行

advance 自動実行

ログ出力

実装しない

自動ループ

非同期処理

停止ボタン

API化

並列処理

4.4 実装方針
subprocess 実行
claude -p --permission-mode bypassPermissions

cwd = repo_path

promptはPythonから渡す

1ステップ限定

現在の next_role のみ実行

ループしない

エラー時停止

以下で停止:

show-next失敗

Claude実行失敗

JSON未生成

validate失敗

advance失敗

4.5 対象ファイル
更新
src\claude_orchestrator\gui\main_window.py
src\claude_orchestrator\gui\ui_sections.py
新規
src\claude_orchestrator\gui\claude_runner.py
4.6 ファイル役割
claude_runner.py

claude subprocess 実行

prompt入力

stdout / stderr / returncode 取得

ui_sections.py

「Claude実行（1ステップ）」ボタン追加

main_window.py

ボタンイベント追加

実行フロー統合

処理手順:

show-next

prompt取得

claude実行

JSON存在確認

validate

advance

UI更新

4.7 ログ方針

出力内容:

Claude実行開始

Claude実行完了

JSON保存確認

validate結果

advance結果

4.8 完了条件

以下を満たす:

ボタン追加済み

implementer で成功

reviewer で成功

director で成功

completed 到達

4.9 注意事項

既存機能は残す

main_windowを肥大化させない

例外は必ずログ出力

ファイルは全文出力

相対パスコメント必須

5. 次の段階（参考）

将来的に:

自動ループ実行

非同期実行

停止ボタン

Claude API 直接連携

実行履歴管理

まとめ

現在の状態は

「AIを手動で回すGUI」

次のステップは

「AIを自動で回すオーケストレーター」

への進化である。
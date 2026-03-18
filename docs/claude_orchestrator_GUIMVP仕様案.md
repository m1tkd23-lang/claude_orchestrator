<!-- docs\claude_orchestrator_GUIMVP仕様案.md -->
# claude_orchestrator GUI MVP仕様案

## 1. 目的

本GUIの目的は、claude_orchestrator の既存CLI/usecaseを再利用しながら、  
1つの task を人手で安全に前進させる操作盤を提供することである。

対象とする運用は、現行の半自動ワークフローとする。

### 想定フロー

- Python側で prompt を生成
- 人が Claude Code に貼り付け
- Claude が JSON report を返す
- 人が JSON を保存する
- Python側で validate / advance を行う

本GUIは、この流れを見やすく、間違えにくく、繰り返しやすくすることを目的とする。

---

## 2. MVPの範囲

今回のGUI MVPでは、以下を対象とする。

### 対象機能

- 対象 repo の指定
- `.claude_orchestrator` 初期化
- task 一覧表示
- task 詳細表示
- 新規 task 作成
- 次 role 向け prompt 生成
- 生成済み prompt の表示
- 次に保存すべき report JSON パス表示
- report 検証
- task 状態前進
- 実行ログ表示

### 対象外

- Claude Code の自動起動
- クリップボード自動貼り付け
- Enter 自動送信
- Claude セッション監視
- 複数 repo 同時管理
- 複数 task 並列操作の高度UI
- runtime ログ監視の自動更新
- task 削除 / archive
- blocked 再開専用UI
- diff 表示
- report JSON 編集支援

---

## 3. 実装方針

### 3-1. GUIフレームワーク

PySide6 を採用する。

### 3-2. ロジック呼び出し方式

GUIは CLI を subprocess で呼ばない。  
GUIは application/usecases を直接呼ぶ。

### 使用usecase

- InitProjectUseCase
- CreateTaskUseCase
- StatusUseCase
- ShowNextUseCase
- ValidateReportUseCase
- AdvanceTaskUseCase

### 3-3. GUI層の責務

GUI層は以下のみ行う。

- 入力受付
- usecase 呼び出し
- 結果表示
- エラー表示
- ログ表示
- 画面状態更新

GUI層に workflow 判定や独自業務ロジックは持たせない。

---

## 4. 画面構成

MVPでは単一メインウィンドウ構成とする。

大きく3ペイン構成を想定する。

### 左ペイン

- repo 操作
- task 一覧
- task 作成

### 中央ペイン

- task 詳細
- 現在状態
- 操作ボタン

### 右ペイン

- prompt 表示
- output JSON path 表示
- 実行ログ表示

---

## 5. 画面要素詳細

### 5-1. repo操作エリア

#### 表示項目

- repo パス入力欄
- 参照ボタン
- 初期化確認ボタン
- init-project 実行ボタン

#### 動作

##### repoパス入力

ユーザーが対象 repo のパスを入力する。

##### 参照

ディレクトリ選択ダイアログを開く。

##### 初期化確認

- `.claude_orchestrator` の存在確認
- `project_config.json` の存在確認
- 結果をログに出す

##### init-project 実行

`InitProjectUseCase.execute(repo_path, force=False)` を実行する。

既に存在する場合はエラー表示。  
将来的に force は別導線にするが、MVPでは通常初期化のみとする。

### 5-2. task一覧エリア

#### 表示項目

- task 一覧リスト
- 更新ボタン

#### 一覧表示内容

各行に最低限これを出す。

- task_id
- status
- current_stage
- next_role
- cycle
- title

#### 動作

##### 更新

`StatusUseCase.list_tasks(repo_path)` を呼ぶ。  
task一覧を再描画する。

##### task選択

選択された task の詳細を中央ペインへ表示する。

### 5-3. task作成エリア

#### 表示項目

- title 入力欄
- description 入力欄
- context_files 入力欄
- constraints 入力欄
- task作成ボタン

#### MVP時点の入力方式

- context_files は複数行テキスト
- constraints も複数行テキスト
- 1行1項目として list 化する

#### 動作

##### task作成

`CreateTaskUseCase.execute(...)` を実行する。

成功時:

- ログ出力
- task一覧再読込
- 新規taskを選択状態にする

失敗時:

- エラー表示

### 5-4. task詳細エリア

#### 表示項目

- task_id
- title
- description
- status
- current_stage
- next_role
- cycle
- last_completed_role
- max_cycles
- task_dir

#### 動作

`StatusUseCase.get_task_status(repo_path, task_id)` の結果を表示する。

### 5-5. 操作エリア

#### ボタン

- show-next
- validate-report
- advance
- 再読込

#### show-next

##### 動作

`ShowNextUseCase.execute(repo_path, task_id)` を実行する。

成功時:

- role
- cycle
- prompt_path
- output_json_path

を画面に表示する。  
prompt本文も右ペインへ表示する。

##### 補足

`ShowNextUseCase` は promptファイルを書き出すだけで本文は返していないため、  
GUI側で `prompt_path` を開いて本文を表示する。

#### validate-report

##### 動作

現在の `next_role` を対象 role として検証する。  
`ValidateReportUseCase.execute(repo_path, task_id, role)` を実行する。

成功時:

- `valid=True` を表示
- `report_path` を表示
- ログへ記録

失敗時:

- エラー内容をログとメッセージ表示

#### advance

##### 動作

`AdvanceTaskUseCase.execute(repo_path, task_id)` を実行する。

成功時:

- state表示更新
- task一覧更新
- ログへ記録

失敗時:

- エラー表示

#### 再読込

- task詳細
- task一覧
- prompt表示

を再読込する。

### 5-6. prompt表示エリア

#### 表示項目

- 現在の prompt path
- prompt本文表示欄（読み取り専用）

#### 動作

show-next 成功後に最新 prompt を表示する。  
読み取り専用テキストエリアとする。

#### MVPでは未実装

- 自動クリップボードコピー
- Markdown装飾
- 差分表示

### 5-7. output JSON path 表示エリア

#### 表示項目

- 次に保存すべき report JSON ファイルパス

#### 目的

人が Claude の JSON をどこへ保存するかを迷わないようにする。

#### MVPでは未実装

- JSON貼り付け保存ボタン
- 自動整形保存

### 5-8. ログ表示エリア

#### 表示内容

時系列で以下を表示する。

- 実行コマンド相当の操作
- 成功メッセージ
- エラーメッセージ
- 対象 task_id
- 対象 role
- 対象 path

#### 例

- repo initialized
- task created
- show-next completed
- validate success
- advance success
- JSON parse failed
- schema validation failed

ログはMVPでは画面内の一時ログでよい。  
ファイル永続化は今回の対象外とする。

---

## 6. 状態遷移と画面反映

### 6-1. 基本原則

画面は `state.json` を唯一の状態基準とする。

### 表示対象

- status
- current_stage
- next_role
- cycle
- last_completed_role

### 6-2. show-next後

- prompt表示更新
- output JSON path 更新
- 現在task詳細は変更しない

### 6-3. validate後

状態は変化しない。  
validation結果のみ表示する。

### 6-4. advance後

- task詳細を更新
- task一覧を更新
- next_role 変化を反映
- cycle増加があれば反映

---

## 7. エラー表示方針

MVPでも、エラーはなるべく人間が読めるようにする。

### 7-1. 想定エラー

- repo未指定
- repoパス不正
- `.claude_orchestrator` 未初期化
- task未選択
- reportファイル未存在
- JSON parse失敗
- schema不一致
- task_id不一致
- role不一致
- cycle不一致
- すでに終了済み task に対する show-next / advance

### 7-2. 表示方法

#### 軽いエラー

- ログ欄へ出す
- 必要に応じてステータスラベルに表示

#### 強いエラー

- QMessageBox で表示
- あわせてログ欄にも記録

### 7-3. メッセージ例

- Task directory not found
- Report file not found
- task_id mismatch
- role mismatch
- cycle mismatch
- Unsupported role
- Task already finished or blocked

---

## 8. MVPでの入力制約

### 8-1. repo

- ディレクトリであること
- 読み書き可能であることが望ましい

### 8-2. task作成

- title は必須
- description は必須
- context_files / constraints は任意

### 8-3. validate / advance

- task が選択されていること
- repo が有効であること

---

## 9. 内部構成案

### 9-1. 想定ファイル

- `apps\gui_main.py`
- `src\claude_orchestrator\gui\__init__.py`
- `src\claude_orchestrator\gui\main_window.py`

MVPではまずこの程度でよい。

### 9-2. 将来分割候補

- `src\claude_orchestrator\gui\widgets\...`
- `src\claude_orchestrator\gui\dialogs\...`
- `src\claude_orchestrator\gui\helpers\...`

ただしMVP時点では分割しすぎない。

---

## 10. 実装時に必要な依存修正

現状コードから見て、少なくとも以下は必要。

### 追加候補

- PySide6
- jsonschema

`jsonschema` は SchemaValidator が使っているので必須です。  
ここが抜けたままGUIに進むと、validate ボタンが突然転ぶという、実に気まずい芸を見せます。

---

## 11. 手動E2E試験シナリオ

### 11-1. 正常完了フロー

1. repo選択
2. init-project
3. task作成
4. task選択
5. show-next
6. promptをClaudeへ貼り付け
7. task_router JSON保存
8. validate-report
9. advance
10. implementer で同様
11. reviewer で同様
12. director で同様
13. approve で completed 確認

### 11-2. reviseフロー

1. director report の `final_action = revise`
2. advance
3. cycle が `+1` される
4. `next_role` が `task_router` に戻る
5. 次サイクルは `task_router → implementer → reviewer → director` の順で再開する

### 11-3. 異常系

- report未保存のまま validate
- 壊れたJSONで validate
- role違いJSONで validate
- cycle違いJSONで validate
- 完了済みtaskに show-next

---

## 12. 今回のMVP完了条件

以下を満たせばGUI MVP完了とする。

- repo選択ができる
- init-project が実行できる
- task作成ができる
- task一覧が見える
- task詳細が見える
- show-next で prompt生成と表示ができる
- output JSON path を確認できる
- validate-report が実行できる
- advance が実行できる
- completed / revise の両パターンをGUI経由で確認できる

---

## 13. 次段階で追加したいもの

MVP後の自然な拡張候補です。

- promptコピー機能
- report JSON 貼り付け保存機能
- validation失敗箇所の詳細表示
- status色分け
- blocked task 強調表示
- force init-project
- task archive / delete
- ログ永続化
- 複数ペイン改善
- recent repo 履歴

---
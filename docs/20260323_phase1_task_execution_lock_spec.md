# docs\phase1_task_execution_lock_spec.md
# Phase 1 実装仕様書: task 実行ロック導入

## 目的
- GUI と remote session が同一 task を同時に進めることを防ぐ。
- 実行開始主体が GUI なのか remote session なのかを明示して記録する。
- Phase 1 では **task 実行系の排他** のみ導入し、次タスク承認は後続 Phase で共通 usecase 化する。

## 背景
現状の `RunTaskUseCase` は 1 回の実行中に `show-next -> claude -> validate-report -> advance` を順に進めるが、各段階で state / report を別タイミングで参照する。GUI auto-run と remote operator が同一 task を同時に進めると、片方が state を更新した後に、もう片方が古い前提で report を探しに行き、`director_report_v1.json not found` のような不整合が起こりうる。

## Phase 1 のスコープ
### 入れるもの
- task 単位ロックファイル
- 実行主体情報の記録 (`gui` / `remote` / `cli`)
- `RunTaskUseCase.execute()` 開始時のロック取得
- `RunTaskUseCase.execute()` 終了時のロック解放
- GUI 側の owner 付与
- remote 側で呼ぶための引数仕様

### まだ入れないもの
- role / cycle 固定の厳密検証
- `state_revision` 追加
- 承認待ち状態の共通 usecase 化
- controller.py の画面分割

## 追加ファイル
- `src/claude_orchestrator/infrastructure/task_execution_lock.py`

## 変更ファイル
- `src/claude_orchestrator/application/usecases/run_task_usecase.py`
- `src/claude_orchestrator/gui/auto_run_worker.py`
- `src/claude_orchestrator/application/remote_operator/controller.py`（実行開始 2 箇所のみ）

## ロックファイル仕様
配置:
- `.claude_orchestrator/tasks/<TASK-ID>/runtime_lock.json`

保持項目:
- `task_id`
- `owner_type`: `gui` / `remote` / `cli` / `unknown`
- `owner_id`: 例 `gui-main-window`, `remote:<session_name>`
- `owner_label`: 画面表示向け
- `status`: `running`
- `started_at`
- `updated_at`
- `repo_path`

## 挙動
### 実行開始
`RunTaskUseCase.execute()` の入口で lock 取得を試みる。

- ロック無し: 取得して続行
- 同一 owner のロック: 再入を許可せず、そのまま続行扱い
- 別 owner のロック: `TaskExecutionLockedError` を送出

### 実行終了
`finally` で lock を解放する。

### completed task
`next_role == none` で即 return する場合も、ロック取得後に finally で解放する。

## GUI owner 仕様
GUI worker は以下で実行する。
- `executor_type="gui"`
- `executor_id="gui-main-window"`
- `executor_label="GUI"`

## remote owner 仕様
remote operator は以下で実行する。
- `executor_type="remote"`
- `executor_id=f"remote:{session_name or 'unknown'}"`
- `executor_label=f"Remote({session_name or 'unknown'})"`

## エラー文言方針
別 owner がロック中なら、例外メッセージに少なくとも以下を含める。
- task_id
- 実行中 owner_label
- started_at

例:
`Task is already running by Remote(my-session): TASK-0024`

## controller.py への適用範囲
Phase 1 では `controller.py` 全分割はまだ行わず、次の 2 箇所だけ owner 情報付きに置換する。
- `_run_task_and_render()` 内の `RunTaskUseCase().execute(...)`
- `_run_standard_task_pipeline_and_render()` 内の `RunTaskUseCase().execute(...)`

## テスト観点
1. GUI 実行中に remote 実行開始でロックエラー
2. remote 実行中に GUI 実行開始でロックエラー
3. completed task 実行時に lock が残らない
4. 例外終了時に lock が残らない
5. 同一 owner の単発実行は正常動作
# docs\phase2_role_cycle_fix_spec.md
# Phase 2 実装仕様書: role / cycle 固定

## 目的
- show-next 時点で確定した role / cycle を、その後の validate-report / advance まで一貫して使う。
- 実行途中で state.json が別操作により変化しても、別 role / 別 cycle の report を誤って読まないようにする。
- Phase 1 の task 実行ロックに加えて、Phase 2 では「処理対象の role / cycle の整合性」を守る。

## 背景
従来は以下の流れになっていた。

1. ShowNextUseCase が state.json を読んで role / cycle を決定
2. Claude 実行
3. ValidateReportUseCase が再び state.json を読んで cycle を決定
4. AdvanceTaskUseCase も再び state.json を読んで role / cycle を決定

この構造では、show-next 後に state.json が変化した場合、
- validate で別 cycle を見る
- advance で別 role を見る
というズレが起こりうる。

## 今回の変更方針

### 1. ShowNextUseCase
- show-next 時点の state から `role` と `cycle` を確定する
- 返却値に `state_snapshot` を追加する
- `state_snapshot` には最低限以下を含める
  - `current_stage`
  - `next_role`
  - `cycle`
  - `status`
  - `last_completed_role`

### 2. ValidateReportUseCase
- `expected_cycle` を必須引数にする
- report パスは `role + expected_cycle` で固定する
- state.json から cycle を再取得しない
- identity check は
  - task_id
  - role
  - cycle
 で判定する

### 3. AdvanceTaskUseCase
- `expected_role`
- `expected_cycle`
を必須引数にする
- 現 state を読み、
  - `state["next_role"] == expected_role`
  - `state["cycle"] == expected_cycle`
でなければ中断する
- validate も同じ `expected_role / expected_cycle` を渡して行う
- report も `expected_role / expected_cycle` のファイルを読む

### 4. RunTaskUseCase
- ShowNextUseCase の返却値から `role` と `cycle` を受け取る
- ValidateReportUseCase に `expected_cycle=cycle` を渡す
- AdvanceTaskUseCase に
  - `expected_role=role`
  - `expected_cycle=int(cycle)`
を渡す

## 期待される効果
- show-next で決まった role / cycle が最後まで固定される
- state が途中で変化しても、advance 側で不一致検知して止まる
- `director_report_v1.json not found` のような「別 role / 別 cycle を探しに行く」系の再発を減らせる

## 今回まだ入れないもの
- state_revision の明示追加
- CLI の validate-report / advance コマンド引数拡張
- 承認 usecase 共通化

## テスト観点
1. 通常系
   - show-next → claude → validate → advance が従来通り通る
2. report identity mismatch
   - report 内の cycle を意図的に変えた場合に validate で落ちる
3. state drift
   - show-next 後に state.json の next_role または cycle を変更した場合に advance で落ちる
4. completed task
   - next_role=none の task は従来通り completed を返す
# docs\phase3_revision_guard_spec.md
# Phase 3 実装仕様書: revision 管理

## 目的
- show-next 時点の state を `revision` で固定し、validate / advance の両方で競合検知する。
- GUI / remote の併用時に、途中で state.json が別処理に更新された場合でも安全に停止する。
- Phase 1 の task 実行ロック、Phase 2 の role / cycle 固定に加えて、Phase 3 では state の更新競合を検知する。

## 背景
現状は Phase 2 により role / cycle は固定されているが、state.json 自体の更新世代は追跡していない。
このため、まれに以下の競合が残る。

1. show-next で role / cycle を確定
2. 別処理が state.json を更新
3. validate では report 自体は正しい
4. しかし現在の state はすでに別世代

このズレを検知するため、state.json に `revision` を持たせる。

## 変更方針

### 1. state.json
- `revision` を追加する
- 初期値は `1`

### 2. ShowNextUseCase
- `state_snapshot` に `revision` を追加する
- 返却値トップレベルにも `revision` を含める

### 3. ValidateReportUseCase
- `expected_revision` を必須引数にする
- 現在の state.json を読み、`revision == expected_revision` を確認する
- 不一致なら validation 失敗とする
- これにより validate 段階で早期に state drift を検知できる

### 4. AdvanceTaskUseCase
- `expected_role`
- `expected_cycle`
- `expected_revision`
を必須引数にする
- 現在の state.json を読み、
  - `next_role == expected_role`
  - `cycle == expected_cycle`
  - `revision == expected_revision`
を満たさない場合は中断する
- state 更新成功時は `revision + 1` を書き込む

### 5. RunTaskUseCase
- ShowNextUseCase の返却値から `revision` を受け取る
- ValidateReportUseCase に `expected_revision=revision`
- AdvanceTaskUseCase に `expected_revision=revision`
を渡す

## 期待効果
- validate で早期に競合を検知できる
- advance でも最終防衛線として競合を検知できる
- state 更新時に revision が増えるため、古い show-next 結果を使った進行を防げる

## テスト観点
1. 通常系
   - show-next → validate → advance が成功し、state revision が +1 される
2. validate drift
   - show-next 後に state revision を変えたら validate で落ちる
3. advance drift
   - validate 後に state revision を変えたら advance で落ちる
4. 初期 state
   - 新規 task 作成時の state.json に revision=1 が入る
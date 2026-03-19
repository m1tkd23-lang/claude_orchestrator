# src\claude_orchestrator\template_assets\project_bundle\.claude_orchestrator\skills\task_router\route-task.md
# route-task

task_router 用の固定 skill です。

## 目的

新規 task を実装開始前に整理し、  
各 role が使うべき skill を最小限で決めること。

## 入力として確認するもの

- task title
- task description
- context_files
- constraints

---

## 判断手順

### 1. task の主目的を判定する

- 新機能追加なら `feature`
- 不具合修正なら `bugfix`
- 構造整理なら `refactor`
- 文書更新中心なら `docs`
- 調査中心なら `research`
- 雑多な整備なら `chore`

### 2. 影響範囲から risk_level を判定する

- `low`
  - 変更対象が限定的
  - 局所的
  - 既存構造への影響が小さい
  - 読み取り確認や最小タスク中心
- `medium`
  - 複数ファイル変更
  - UIやフローに影響
  - 既存挙動への注意が必要
- `high`
  - workflow / schema / state / core 処理に影響
  - 破壊的変更の危険が高い
  - 設計の再確認が重要

### 3. role ごとの skill を決める

#### implementer
- 実装前の方針整理が必要なら `write-plan`
- 実装本体または実行確認が必要なら `execute-plan`
- bugfix で原因切り分け中心なら `debug-fix` を検討
- DB / schema / migration 系なら `migration-safety-check` を検討

#### reviewer
- 通常は `code-review`
- task_type が `docs` または `research` のときは `code-review` の代わりに `doc-consistency-review` を付与する

#### director
- 最初は空配列でもよい

### 4. skill は最小限にする

- 何でも多く付けない
- 明確な理由があるものだけ付ける
- 「とりあえず付ける」をしない
- role_skill_plan には現在 repo 内に存在する skill のみを含める（存在しない skill を含めると実行時エラーになる）
- 新しい skill が必要と判断した場合は即付与せず、skill_selection_reason または initial_execution_notes で「新規 skill 候補」として提案する

### 5. implementer 開始前の注意点を書く

- 壊してはいけない導線
- 影響範囲の確認観点
- 保守的に進めるべき点
- 不明点が残る場合の注意
- GUI起動確認や長時間プロセスを伴う task では、auto-run の timeout に抵触しないよう initial_execution_notes に明記すること（起動確認後は速やかにプロセスを終了する旨を含めること）

---

## このファイルの役割

このファイルは task_router が毎回参照する**実装手順**です。
routing 判断の手順と skill 付与条件を操作レベルで定義します。

skill 全体の設計方針・付与条件の正の定義・新規追加方針については
[docs/skill_design.md](../../../../docs/skill_design.md) を参照してください。
本ファイルの付与条件は skill_design.md の内容に従って維持します。

---

## skill 付与条件一覧

### write-plan を付与する条件

以下のいずれかに当てはまる場合に付与する。

- 複数ファイル変更が想定される
- 実装前に変更方針整理が必要
- UI / workflow / schema を変更する
- task_type が `feature` または `refactor`
- 変更範囲を誤ると壊しやすい

### write-plan を付与しない条件

以下のような場合は通常付与しない。

- 調査や確認のみが目的
- 既存コードの読み取り中心
- 最小の research task
- 実装方針の整理より確認作業本体が中心

### execute-plan を付与する条件

以下のいずれかに当てはまる場合に付与する。

- 実装作業本体がある
- 動作確認や検証作業本体がある
- write-plan の後に実行フェーズが必要
- task_type が `feature` / `bugfix` / `refactor` / `research` / `docs`（実体書き込みがある場合）

### execute-plan を付与しない条件

以下のような場合は通常付与しない。

- implementer が実質的に動かない task
- director 判断のみが主目的
- task_router で blocked にすべき状態

### debug-fix を付与する条件

以下のいずれかに当てはまる場合に検討する。

- task_type が `bugfix`
- 原因特定が主目的
- 再現条件、原因調査、切り分けが必要
- 修正前に問題箇所を特定しないと危険

### migration-safety-check を付与する条件

以下のいずれかに当てはまる場合に検討する。

- schema / migration / state / 保存形式の変更がある
- 後方互換性が問題になりうる
- 既存 task / 既存 data への影響確認が必要

### code-review を付与する条件

以下の方針で扱う。

- reviewer が動く通常 task では原則付与する
- feature / bugfix / refactor / chore の通常 flow では付与する
- docs / research の場合は `doc-consistency-review` を代わりに付与し、`code-review` は付与しない
- reviewer を完全に省くような特殊運用をしない限り、基本付与する

### doc-consistency-review を付与する条件

以下の条件で付与する。

- task_type が `docs` または `research` のとき reviewer に付与する
- 変更対象が主に markdown / テキスト / ルール定義ファイルであるとき
- コードレビューより文書整合性の確認が主眼となるとき

### director 用 skill の扱い

- 現段階では director は空配列でよい
- 今後、director に定型判断手順が必要になった場合のみ追加する

---

## 出力方針

- role_skill_plan は implementer / reviewer / director を必ず含める
- skill_selection_reason は配列で具体的に書く
- initial_execution_notes は implementer がすぐ読んで役立つ内容にする
- used_skills には `route-task` を入れる
- 安全に routing できないときは `blocked` にする

---

## 現在利用可能な skill

| role | skill |
|------|-------|
| task_router | `route-task` |
| implementer | `write-plan` / `execute-plan` / `debug-fix` / `migration-safety-check` |
| reviewer | `code-review` / `doc-consistency-review` |

---

## 運用メモ

- skill は人が追加する
- 新しい skill を追加したら、このファイルの「現在利用可能な skill」一覧と付与条件を更新する
- task を数件回し、想定とズレたら条件文を更新する
- task_router 自体を育てる前提で運用する
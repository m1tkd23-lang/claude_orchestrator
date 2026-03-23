<!-- .claude_orchestrator/skills/task_router/route-task.md -->
# route-task

task_router 用の固定 skill です。

## 目的

新規 task を実装開始前に整理し、  
各 role が使うべき skill を最小限で決めること。

同時に、  
description / constraints / context_files / 完了意図 の整合を確認し、  
安全に実行できない task を ready にしないこと。

## 入力として確認するもの

- task title
- task description
- context_files
- constraints

---

## 判断手順

### 0. 実行可能性と整合の事前確認を行う

最初に以下を確認する。

- constraints 同士に矛盾がないか
- task description と constraints が両立しているか
- 完了意図と禁止事項が両立しているか
- 実行に必要な context_files が不足していないか
- 未確定事項を断定前提にしないと進められない状態ではないか
- 実在確認できないファイル・skill・前提に依存していないか
- implementer が着手可能な粒度まで task が整理されているか

#### 代表的な矛盾例

- 「A を requirements-dev に分離する」と「requirements.txt だけで A を使える状態にする」
- 「コードを変更しない」と「既存コード修正を完了条件に含める」
- 「実装しない」と「動作する実装を成果物に含める」
- 「未確定事項を固定しない」と「未確定仕様を断定して設計・実装する」

#### constraints 矛盾の検出パターン

以下のパターンが存在する場合は矛盾として blocked を検討する。

- 同一ファイル・対象に「変更する」と「変更しない」の両方が要求されている
- 「X を Y に移動する」と「X を移動前の場所でそのまま使い続ける」が共存している
- constraints 間で同一対象に対して相反する動詞が使われている（追加/削除、分離/統合、変更/維持など）
- 複数の constraints が互いに排他的な完了状態を同時に要求している

#### description / constraints 整合チェックのパターン

以下が当てはまる場合は整合不良として blocked を検討する。

- description に「実装する」とあるのに constraints に「コードを変更しない」がある
- description の完了意図が constraints で明示的に禁止されている
- description が前提とするファイル・機能が constraints の禁止対象と重なっている

#### 実行不能条件の検出パターン

以下が当てはまる場合は実行不能として blocked を検討する。

- 未存在のファイル・モジュール・skill を前提としないと進められない
- 成功基準が「曖昧な改善」にとどまり、implementer が完了を判断できない
- 実装範囲が未定義のまま「全ての XX を変更する」のような条件が成功基準になっている

#### この段階の判断

- 明確な矛盾や不足がある場合は `blocked`
- 判断可能なら次へ進む

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

### 6. blocked にする場合は、次に必要な修正・確認内容を具体化する

blocked にする場合は、単に止めるのではなく次を明記する。

- 何が矛盾しているか
- 何が不足しているか
- 何を確認すれば ready にできるか
- constraints をどう整理すべきか
- context_files のどれが不足しているか

**skill_selection_reason に含めるべき情報:**

- どの constraints または description の記述が矛盾・不足・未確定の原因か（具体的な言及が望ましい）
- 具体的にどのような矛盾が発生しているか（「制約A と 制約B が共存できない」という形式が望ましい）
- 実在確認できないファイル・skill・前提がある場合はその名称

**initial_execution_notes に含めるべき情報:**

- 何を修正・確認すれば ready にできるか（例: 「制約X を削除する」「context_files に Y を追加する」）
- constraints をどのように整理・分割すれば矛盾が解消されるか
- ready にするために決定が必要な未確定事項の具体的なリスト

blocked の理由が複数ある場合はすべて列挙すること。
空の配列や曖昧な一行で済ませず、次に人または後続工程が判断できる材料を残すこと。

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
- blocked にする場合は、矛盾・不足・未確定事項を具体的に残す
- ready にする場合は、implementer が着手できる程度まで task を整理する

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
- constraints の矛盾や実行不能条件を見逃した場合は、このファイルの判断手順を先に改善する
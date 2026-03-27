# role別最小参照マップ

## 基本方針

- 必要最小限のファイルのみ参照する
- 不要な探索を行わない
- 「参照できる」ことと「常時渡す」ことを分けて考える
- prompt を重くしすぎず、判断に必要な材料だけを渡す

---

## task_router

### 必須
- task.json
- state.json
- role定義
- schema
- route-task skill
- completion_definition
- task_splitting_rules

### 条件付き
- context_files
- constraints関連ファイル
- core docs

### 通常不要
- reviewer report
- director report
- 無関係な過去TASK全文

### task_router 用の補足
- completion_definition は、この task が完成条件のどこに寄与するかを判断するために使う
- task_splitting_rules は、粒度が大きすぎないか、統合確認を別 task に切るべきかを判断するために使う

---

## implementer

### 必須
- task.json
- state.json
- 前cycle director report
- assigned skills

### 条件付き
- context_files
- 実装対象ファイル

### 通常不要
- reviewer report
- 無関係な過去TASK
- repo全探索

---

## reviewer

### 必須
- task.json
- state.json
- implementer report
- assigned skills

### 条件付き
- changed_files
- 変更対象の実ファイル

### 通常不要
- director report
- 過去TASK全文
- repo全探索

---

## director

### 必須
- task.json
- state.json
- implementer report
- reviewer report

### 通常不要
- repo全体探索
- 詳細実装再確認
- 無関係な docs 全文

---

## planner

### 必須
- source task.json
- source state.json
- implementer / reviewer / director report
- task list summary（軽量一覧）
- core docs
- completion_definition
- feature_inventory
- 必要最小限の reference docs

### 補完用の常時参照候補
- `.claude_orchestrator/docs/task_history/過去TASK作業記録.md`

### 条件付き
- README.md
- source task に直接関係する docs
- 人が明示した reference docs

### 通常不要
- 実装コード全文
- 無関係なTASK
- task ディレクトリ全文走査
- task list の詳細フルダンプ

### planner 用の補足
- `task list summary` は重複回避と進捗把握のための**軽量一覧**として使う
- 過去の細かい知見や再利用メモは `過去TASK作業記録.md` で補う
- `completion_definition` は完成条件との距離を測るために使う
- `feature_inventory` は既実装 / GUI未接続 / 未実装 / 対象外を区別するために使う
- 「一覧」と「知見」を分離して渡すことで prompt 肥大化を抑える

---

## plan_director

### 必須
- source task.json
- source state.json
- implementer / reviewer / director report
- planner_safe / planner_improvement report
- proposal states
- task list summary（軽量一覧）
- completion_definition
- feature_inventory

### 条件付き
- source task に直接関係する最小限の docs

### 通常不要
- 実装コード全文
- 過去TASK全文
- 無関係な reference docs 大量投入

### plan_director 用の補足
- plan_director は proposal 比較が主目的なので、planner よりさらに入力を広げすぎない
- `completion_definition` は完成条件への寄与度を比較するために使う
- `feature_inventory` は重複 proposal や順序不整合を避けるために使う
- 既存 proposal と source task の文脈判断に不要な全文資料は原則渡さない
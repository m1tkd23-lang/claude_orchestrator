# planner / task_router 判断材料マップ

## task_router

### 判断対象
- title
- description
- context_files
- constraints
- core docs
- 固定 skill

---

### 判断内容

#### task_type
- feature / bugfix / refactor / docs / research / chore

#### risk_level
- low / medium / high

#### skill選定
- 最小限
- 実在するskillのみ

---

### 注意点
- 過剰skill付与禁止
- 不明点が多い場合は blocked
- initial_execution_notes を具体的に書く
- 不足ファイルがある場合は context_files を疑う
- repo 全探索を前提にしない

---

## planner

### 判断対象
- source task
- implementer / reviewer / director report
- task list summary
- core docs
- reference docs
- 必要に応じて task_history

---

### 判断内容
- 次task候補（1〜3件）
- priority設定
- context_files明確化
- constraints具体化
- 重複提案回避
- mainline / maintenance の整合

---

### task list summary の扱い
- task list summary は**軽量一覧**として使う
- 一覧の目的は、過去 task の存在確認、進捗把握、重複提案回避
- 過去 task の細かな知見や注意点まで task list summary に持たせない
- 細かな知見は `.claude_orchestrator/docs/task_history/過去TASK作業記録.md` で補う

---

### 注意点
- 抽象的提案禁止
- 重複提案禁止
- 実在しないファイル禁止
- task粒度を適切にする
- 無関係な docs を大量に読ませない
- 一覧データと知見データを混同しない

---

## よくある失敗

### task_router
- skill過多
- risk過小評価
- 不明点無視
- context_files 不足を見落とす

### planner
- 抽象案のみ
- 巨大task化
- context_files曖昧
- task list summary に履歴の全てを持たせようとして prompt を重くする
- 過去TASK作業記録を使わずに重複提案する
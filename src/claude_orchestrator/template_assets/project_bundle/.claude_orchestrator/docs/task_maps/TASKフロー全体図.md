# TASKフロー全体図

## 1. TASK開始

- task.json 作成
- state.json 作成
- next_role = task_router

---

## 2. 実行サイクル

各roleは以下の流れで実行される。

1. prompt生成
2. Claude実行
3. report出力
4. validate
5. state更新

---

## 3. role遷移

task_router → implementer → reviewer → director

---

## 4. roleごとの出力

### task_router
- task_type
- risk_level
- role_skill_plan

### implementer
- changed_files
- commands_run
- results

### reviewer
- decision（ok / needs_fix / blocked）

### director
- final_action（approve / revise / stop）

---

## 5. サイクル制御

### approve
→ TASK完了

### revise
→ 次cycleの task_router へ戻る

### stop
→ TASK停止

---

## 6. plannerフロー（別系統）

1. completed task 読込
2. planner report 生成
3. proposal一覧化
4. proposal選択
5. 新task生成

### planner入力の考え方
- `task list summary` は全 task の軽量一覧を渡す
- 過去の詳細知見は `.claude_orchestrator/docs/task_history/過去TASK作業記録.md` で補う
- これにより、重複提案回避に必要な情報を保ちつつ prompt の肥大化を抑える

---

## 7. 重要ポイント

- implementer は前cycleの director report を参照する
- reviewer は同cycleの implementer report を参照する
- director は同cycleの両reportを参照する
- planner は source task の3 report と軽量 task 一覧を参照する
- plan_director は planner report 群と proposal state を参照する
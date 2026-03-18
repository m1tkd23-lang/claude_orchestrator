# docs\planner_v1_仕様書.md
# planner v1 仕様書

## 1. 目的

planner ロールは、completed になった task を材料として読み取り、  
**次に実装する価値が高い task 候補を 1〜3 件提案する** ための補助ロールである。

planner は task を自動確定しない。  
planner の役割は **提案** までとし、最終判断は人が行う。

本機能の目的は以下である。

- completed 後の「次に何をやるか」を考える負荷を下げる
- 過去 task と docs を参照した、連続性のある task 候補を生成する
- title / description / context_files / constraints を含む、すぐ task 化しやすい候補を作る
- 採用 / 否決 / 保留の判断を GUI 上で行えるようにする

---

## 2. planner の位置づけ

planner は **次 task 候補の提案者** である。  
planner は **実行 workflow の一部ではない**。

現在の実行 workflow は以下である。

`task_router → implementer → reviewer → director`

planner はこの workflow に含まれず、  
completed task を起点に、次にやる task 候補を提案する補助機能として動く。

### 2-1. task_router との違い

planner と task_router は役割が異なる。

- `planner`
  - completed task を読み、次 task 候補を提案する
  - task を自動確定しない
  - skill を自動決定しない
  - state 遷移を持たない
- `task_router`
  - 新規 task を実装開始前に整理する
  - task_type / risk_level を決める
  - 各 role に必要な skill を決める
  - 実行 workflow の最初に動く

つまり、

- planner = 次 task 候補の提案者
- task_router = 実行前の task 整理者 / skill 配布者

であり、役割は明確に分離される。

---

## 3. 対象範囲

planner v1 で対象とするのは以下である。

- completed task を起点とした次 task 候補の提案
- GUI 上の「次タスク案作成」ボタンからの実行
- planner report JSON の生成と保存
- GUI 上での候補一覧表示
- 候補ごとの採用 / 否決 / 保留
- 採用候補の task 作成欄への転記

planner v1 では以下は対象外とする。

- 候補の自動採用
- planner 実行後の task 自動作成
- completed 後の planner 自動起動
- planner 候補の物理削除
- repo 全体の全文読込
- 実 task 一覧からの task 削除
- planner が skill を決定すること
- planner が state 遷移を変更すること

---

## 4. 基本方針

### 4.1 planner は提案者であり決裁者ではない

planner は次 task の候補を提案するが、  
その候補を採用するかどうかは人が判断する。

### 4.2 planner は completed task の延長線上で提案する

planner は自由発想で無制限に task を提案しない。  
以下を優先する。

- 今回完了した task の自然な次工程
- 実装済み機能の改善
- 現在の docs や設計方針と整合するもの
- repo 内の既存ファイルに紐づくもの

### 4.3 planner は task 化しやすい粒度で出力する

planner の候補は、抽象論ではなく、  
そのまま task 作成欄へ転記できる粒度であることを求める。

### 4.4 planner は skill を決めない

planner は、提案する task に対して  
title / description / context_files / constraints は提案してよいが、  
実行時の skill 決定は行わない。

skill の決定は、実際に task が作成された後、  
task_router が行う。

---

## 5. ユースケース

### 5.1 completed task から次 task 案を作る

1. 人が completed task を選択する
2. 人が「次タスク案作成」ボタンを押す
3. planner が source task と docs を参照して候補を提案する
4. GUI に候補一覧が表示される
5. 人が採用 / 否決 / 保留を選ぶ
6. 採用した候補は新規 task 作成欄へ転記される
7. 人が内容を確認し、必要に応じて修正して task 作成する
8. task 作成後、実行時は task_router が最初に動く

### 5.2 候補を否決する

1. planner が候補を提案する
2. 人が不要と判断した候補を否決する
3. 候補状態は `rejected` になる
4. 候補履歴は残す

### 5.3 候補を保留する

1. planner が候補を提案する
2. 人が今は着手しないと判断した候補を保留する
3. 候補状態は `deferred` になる
4. 後で再確認できる

---

## 6. planner ロールの責務

planner は以下を行う。

- source task の内容を読む
- source task の reports を読む
- 指定 docs を読む
- 必要に応じて task 一覧の概要を読む
- 次に実装する価値が高い候補を 1〜3 件提案する
- 各候補に title / description / context_files / constraints を付与する
- 各候補に優先度と理由を付与する

planner は以下を行わない。

- task.json の作成
- state.json の更新
- task の自動作成
- 候補の自動採用
- workflow 遷移の決定
- role_skill_plan の決定
- used_skills の決定
- 実行時 skill の決定

---

## 7. planner の入力情報

planner v1 では、以下を入力情報とする。

### 7.1 必須入力

- source task の `task.json`
- source task の `state.json`
- source task の implementer report
- source task の reviewer report
- source task の director report
- target repo path

### 7.2 追加入力

- task 一覧の概要
- planner 実行対象 repo の主要 docs

### 7.3 参照対象 docs の基本方針

planner に渡す docs は、repo 内の全 md ではなく、  
**主設計資料として明示されたもの** に限定する。

想定対象例:

- `docs\Claude Orchestrator GUI 開発記録 & 次工程指示書.md`
- `docs\workflow_rules.md`
- `docs\planner_v1_仕様書.md`
- その他、今後 planner 参照対象として登録した md

---

## 8. planner の出力仕様

planner は JSON を 1 件出力する。

### 8.1 planner report の目的

- source task 完了結果の要約
- 次 task 候補一覧の提供

### 8.2 planner report の必須情報

- `source_task_id`
- `role = "planner"`
- `cycle`
- `summary`
- `proposals`

### 8.3 proposals の件数

- 最低 1 件
- 最大 3 件

### 8.4 各 proposal の必須情報

- `proposal_id`
- `title`
- `description`
- `priority`
- `reason`
- `context_files`
- `constraints`

### 8.5 v1 では proposal に含めないもの

以下は v1 では planner proposal に含めない前提とする。

- `role_skill_plan`
- `used_skills`
- 実行 role の決定
- 実行時 skill の決定
- task_type の確定
- risk_level の確定

これらは task 作成後に task_router が扱う。

---

## 9. planner report JSON イメージ

```json
{
  "_meta": {
    "relative_path": ".claude_orchestrator/tasks/TASK-0005/planner/planner_report_v1.json"
  },
  "source_task_id": "TASK-0005",
  "role": "planner",
  "cycle": 1,
  "summary": "QThread 対応と Claude 実行モニタ追加が完了した。主線の自動実行と進行可視化は成立している。",
  "proposals": [
    {
      "proposal_id": "PLAN-0001",
      "title": "Claude実行モニタの文言重複を整理する",
      "description": "advanced to next role の重複表示を削減し、process started などの文言を整理して視認性を改善する。",
      "priority": "high",
      "reason": "既に主線機能は成立しているため、短時間で UX を改善できる。",
      "context_files": [
        "src\\claude_orchestrator\\gui\\auto_run_worker.py",
        "src\\claude_orchestrator\\gui\\main_window.py"
      ],
      "constraints": [
        "自動完了までの既存動作を壊さない",
        "モニタの情報量を減らしすぎない"
      ]
    }
  ]
}
10. planner 候補状態

planner 候補は task ではなく、proposal として状態を持つ。

10.1 proposal state

proposed

accepted

rejected

deferred

10.2 意味

proposed: 新規提案された状態

accepted: 採用された状態

rejected: 否決された状態

deferred: 保留された状態

10.3 v1 の扱い

v1 では proposal 状態を GUI 上で扱えるようにする。
proposal の保存形式は JSON ベースとする。

11. GUI 仕様
11.1 配置

planner v1 の GUI は 詳細タブ に配置する。

追加要素:

「次タスク案作成」ボタン

proposal 一覧

proposal 詳細表示

採用ボタン

否決ボタン

保留ボタン

11.2 採用時の挙動

v1 では、採用時に直接 task 作成しない。
以下を行う。

新規 task 作成欄へ title / description / context_files / constraints を転記する

人が確認後に task 作成ボタンを押す

task 作成後は task_router が最初に動く

11.3 否決時の挙動

proposal state を rejected にする

proposal 履歴は残す

11.4 保留時の挙動

proposal state を deferred にする

後で再確認可能とする

12. planner prompt の基本方針

planner prompt では以下を明示する。

source task 完了結果を踏まえること

docs と過去 task に整合する提案を行うこと

抽象論ではなく task 化しやすい粒度で出すこと

候補は最大 3 件までとすること

実装価値の低い案や重複案を避けること

task を自動確定しないこと

skill を決定しないこと

13. planner schema の基本方針

planner report schema は既存 schema と同様に JSON Schema で定義する。
additionalProperties: true は v1 では許容するが、必須項目は厳密に持つ。

planner は used_skills の記録対象ではない。
planner は実行 workflow の role ではなく、task 候補提案専用の補助 role として扱う。

14. 保存先方針

planner report は source task 配下に保存する。

候補:

.claude_orchestrator/tasks/{task_id}/planner/planner_report_v{cycle}.json

v1 では source task ごとの提案履歴として扱う。

15. 実装対象案
新規

src\claude_orchestrator\application\usecases\generate_next_task_proposals_usecase.py

src\claude_orchestrator\gui\planner_helpers.py

src\claude_orchestrator\gui\proposal_state_store.py

src\claude_orchestrator\template_assets\project_bundle\.claude_orchestrator\roles\planner.md

src\claude_orchestrator\template_assets\project_bundle\.claude_orchestrator\templates\planner_prompt.txt

src\claude_orchestrator\template_assets\project_bundle\.claude_orchestrator\schemas\planner_report.schema.json

更新

src\claude_orchestrator\gui\ui_sections.py

src\claude_orchestrator\gui\main_window.py

必要に応じて status / runtime 関連の補助層

16. v1 でやらないこと

planner の自動起動

planner 候補の自動 task 作成

proposal の物理削除

実 task 一覧からの削除

repo 全体の無制限読込

planner が workflow を変更すること

planner が skill を決定すること

planner が task_router の代わりになること

17. 今後拡張
v2 候補

completed 後の planner 自動起動

採用時の task 自動作成

proposal 履歴一覧

過去採用 / 否決傾向を踏まえた提案最適化

docs 参照対象の設定画面

planner 実行モニタ表示

planner proposal に task_type 候補や想定リスクを補助情報として付与する検討

ただし、v2 以降でも最終的な skill 決定は task_router 側に残す方針を基本とする。

18. 現段階の結論

planner v1 は、AI に次 task を 考えさせる ための機能であるが、
AI に次 task を 確定させる ための機能ではない。

また、planner は task_router の代わりに skill を決める機能ではない。

本機能は以下を両立することを目指す。

completed 後の次工程立案を効率化する

人の最終判断を維持する

task_router を含む現在の role / schema / GUI 構造に自然に接続する

この方針を planner v1 の設計基準とする。
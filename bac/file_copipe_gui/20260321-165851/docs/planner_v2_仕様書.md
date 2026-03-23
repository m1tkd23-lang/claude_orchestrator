1. 目的

planner v2 は、task 実行結果をもとに
継続的に価値のある次タスクを提案し続ける仕組み を構築することを目的とする。

v1 では proposal が task 配下に閉じていたが、
v2 では proposal を 独立した資産として管理 し、

人間による判断

将来的な自動採用

改善提案の蓄積

を可能にする。

2. 全体構造

planner v2 は以下の2系統で構成される。

2.1 planner_safe

主線開発を安定して前進させる

現実的で低リスクな改善を提案する

将来的に自動採用の対象となる

2.2 planner_improvement

中長期的な改善や構造改革を提案する

高リスク・高リターンの案を扱う

原則として人間判断を前提とする

3. proposal 管理方式
3.1 保存先
.claude_orchestrator/proposals/
3.2 ファイル単位

1 proposal = 1ファイル

形式:

proposal_0001.json
proposal_0002.json
4. proposal ID ルール
4.1 ID形式
proposal_0001
proposal_0002
4.2 採番ルール

連番（ゼロパディング4桁）

既存 proposal の最大値 +1

欠番は再利用しない

5. proposal JSON 構造
{
  "_meta": {
    "relative_path": ".claude_orchestrator/proposals/proposal_0001.json"
  },
  "proposal_id": "proposal_0001",
  "planner_type": "safe",
  "source_task_id": "TASK-0001",
  "source_cycle": 1,

  "title": "",
  "description": "",
  "why_now": "",
  "priority": "high",

  "proposal_kind": "safe",
  "reason": "",

  "context_files": [],
  "constraints": [],
  "depends_on": [],

  "state": "proposed",
  "created_task_id": null,

  "created_at": "",
  "updated_at": ""
}
6. proposal フィールド定義
6.1 planner_type

safe

improvement

6.2 proposal_kind

safe

improvement

challenge

6.3 priority

high

medium

low

7. proposal 状態遷移
7.1 state 一覧

proposed

accepted

rejected

deferred

task_created

7.2 遷移
proposed → accepted → task_created
proposed → rejected
proposed → deferred
8. planner report（v2）
8.1 役割

planner report は proposal 本体を持たず、
実行ログとして扱う

8.2 保存先
.claude_orchestrator/tasks/{task_id}/planner/
8.3 内容
{
  "source_task_id": "TASK-0001",
  "role": "planner_safe",
  "cycle": 1,
  "summary": "",
  "generated_proposal_ids": [
    "proposal_0001",
    "proposal_0002"
  ]
}
9. planner 実行フロー

source_task（completed）を読み込む

planner_prompt を生成

Claude 実行

proposal JSON を複数生成

proposals ディレクトリへ保存

planner report を保存

10. proposal → task 化
10.1 処理

proposal を読み込む

CreateTaskUseCase を実行

task を生成

10.2 変換ルール
description
description

[why_now]
why_now
constraints

constraints をそのまま使用

depends_on を追記

depends_on: xxx
11. GUI 振る舞い
11.1 一覧表示

proposals ディレクトリを直接読む

state に応じて表示を変える

11.2 操作

accept → state=accepted

reject → state=rejected

defer → state=deferred

create task → state=task_created

12. v1 からの変更点
項目	v1	v2
保存場所	task配下	proposals独立
proposal構造	report内配列	1ファイル1件
state管理	別JSON	proposal内
planner	単一	2系統
report	本体含む	ログ化
13. 将来拡張
13.1 自動採用

safe + high priority

depends_on が満たされている

13.2 スコアリング

ROI

リスク

実装コスト

13.3 改善ループ

proposal 実績評価

planner の自己改善

14. 禁止事項

proposal から直接 state.json を変更しない

planner が task を確定しない

実在しないファイルを前提にしない

過去 task / docs と矛盾する提案をしない

15. 設計方針

proposal は資産

planner は供給者

task は実行単位

人間は最終判断者（段階的に縮小）
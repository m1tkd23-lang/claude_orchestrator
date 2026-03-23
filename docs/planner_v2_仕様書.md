# docs\planner_v2_仕様書.md
1. 目的

planner v2 は、task 実行結果をもとに
継続的に価値のある次タスクを提案し続ける仕組み を構築することを目的とする。

v1 では proposal が task 配下に閉じていたが、
v2 では proposal を 独立した資産として管理 し、

人間による判断

将来的な自動採用

改善提案の蓄積

を可能にする。

また v2 では、proposal の性格だけでなく、
**現在の開発方針（development_mode）** を planner 判断に反映できるようにする。

これにより、

- 主線を強く押し進める時期
- 保守や改善を優先する時期

を切り替えながら proposal 生成を行えるようにする。

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

8. development_mode

8.1 目的

development_mode は、
**今このプロジェクトで planner / plan_director が何を優先するか**
を決める上位方針である。

planner_type が proposal の性格を表すのに対し、
development_mode は **現在の運用フェーズ** を表す。

8.2 値

mainline

maintenance

8.3 意味

### mainline

主線を強く前進させる時期。

優先するもの:

- 主線機能の完成
- end-to-end の貫通
- 未完成の主要フロー解消
- ユーザーが使える状態への接近

抑制するもの:

- 小粒な改善だけで終わる案
- 改善 task 直後という理由だけの改善継続
- 主線前進にほぼ寄与しない補助的改善

### maintenance

保守・改善・安定化を優先する時期。

優先するもの:

- 低リスク改善
- remaining_risks 回収
- 直前改善の補完
- 運用性、品質、判断精度の向上

8.4 planner_type との違い

planner_type:

- safe
- improvement

これは **どの性格の提案者が出した proposal か** を表す。

development_mode:

- mainline
- maintenance

これは **今どの方針で proposal を評価・優先するか** を表す。

例:

- planner_safe × mainline
  - 安全に主線を前に進める proposal
- planner_safe × maintenance
  - 低リスクな補完・改善 proposal
- planner_improvement × mainline
  - 将来価値として保持する改善 proposal
- planner_improvement × maintenance
  - 現時点で採択候補になりうる改善 proposal

9. planner report（v2）

9.1 役割

planner report は proposal 本体を持たず、
実行ログとして扱う

9.2 保存先

.claude_orchestrator/tasks/{task_id}/planner/

9.3 内容

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

10. planner 実行フロー

source_task（completed）を読み込む

planner_prompt を生成

Claude 実行

proposal JSON を複数生成

proposals ディレクトリへ保存

planner report を保存

このとき planner は以下を入力として受け取る。

- source task
- source state
- implementer / reviewer / director report
- docs
- project_config
- development_mode

11. proposal 生成ルール

11.1 planner_safe

planner_safe は常に安全寄り proposal を出すが、
development_mode に応じて優先順位を変える。

### mainline の場合

- 安全性を保ちつつ主線前進を最優先にする
- 主線の停滞要因を塞ぐ proposal を上位にする
- 改善 task 直後でも、主線完成に直結する proposal を上位にしてよい

### maintenance の場合

- 低リスク改善、補完、安定化を優先する
- 改善 task 直後は改善継続を強く評価してよい

11.2 planner_improvement

planner_improvement は常に改善 proposal を出すが、
development_mode に応じて位置づけを変える。

### mainline の場合

- 将来価値の高い proposal を資産として整理する
- 主線を止める前提で書かない

### maintenance の場合

- 採択候補として改善 proposal を積極的に提案してよい

12. proposal → task 化

12.1 処理

proposal を読み込む

CreateTaskUseCase を実行

task を生成

12.2 変換ルール

description
description

[why_now]
why_now

constraints

constraints をそのまま使用

depends_on を追記

depends_on: xxx

13. GUI 振る舞い

13.1 一覧表示

proposals ディレクトリを直接読む

state に応じて表示を変える

13.2 操作

accept → state=accepted

reject → state=rejected

defer → state=deferred

create task → state=task_created

14. v1 からの変更点

項目	v1	v2
保存場所	task配下	proposals独立
proposal構造	report内配列	1ファイル1件
state管理	別JSON	proposal内
planner	単一	2系統
report	本体含む	ログ化
方針切替	なし	development_mode 追加

15. 将来拡張

15.1 自動採用

safe + high priority

depends_on が満たされている

development_mode と整合している

15.2 スコアリング

ROI

リスク

実装コスト

主線前進量

改善継続価値

15.3 改善ループ

proposal 実績評価

planner の自己改善

15.4 GUI 切替

GUI から development_mode を変更できるようにする

16. 禁止事項

proposal から直接 state.json を変更しない

planner が task を確定しない

実在しないファイルを前提にしない

過去 task / docs と矛盾する提案をしない

development_mode を無視して機械的に同じ傾向の proposal だけを出し続けない

17. 設計方針

proposal は資産

planner は供給者

task は実行単位

人間は最終判断者（段階的に縮小）

planner_type と development_mode は分離する

- planner_type は提案の性格
- development_mode は現在の優先方針

この分離により、
安全寄り運用と主線推進運用を同じ仕組みの上で切り替えられるようにする。
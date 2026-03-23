# docs\workflow_rules.md
# claude_orchestrator ワークフロールール（rev2）

## 1. 目的

本書は、claude_orchestrator における以下を定義する。

- task 実行 workflow の状態遷移
- 各 role の責務 / 禁止事項
- report の必須要件
- validate 条件と工程ゲート
- revise / blocked / stop の扱い
- planner / plan_director における development_mode の扱い

Python 側は本ルールに従って state を更新し、  
Claude は本ルールに従った JSON report を出力する。

本 workflow は、アプリを工場、role を工程、report を工程記録、  
schema / validate / advance を品質保証ゲートとして扱う考え方を前提とする。

---

## 2. 基本構造

1つの task は以下の workflow で処理される。

```text
task_router → implementer → reviewer → director

これを「1サイクル」と呼ぶ。

3. 状態遷移
3-1. 正常系
task_router
  ↓
implementer
  ↓
reviewer
  ↓
director
  ├─ approve → completed
  ├─ revise  → task_router（cycle+1）
  └─ stop    → stopped
3-2. 異常系

以下はすべて処理停止扱いとする。

role	判定値	結果
task_router	blocked	blocked
implementer	blocked / need_input	blocked
reviewer	blocked	blocked
3-3. revise の扱い

director が revise を返した場合は、次を行う。

cycle を +1 する
再開点を task_router に戻す

理由は以下である。

task の再整理
skill の再配布
実行戦略の再構築
場当たり的な再実装の防止
4. 実行フロー（機械処理）

GUI / CLI における処理順は以下とする。

show-next
↓
Claude 実行
↓
report 保存確認
↓
validate-report
↓
advance
↓
state 更新
↓
次 role

終了条件は以下とする。

completed
blocked
stopped
next_role = none
5. validate の責務

validate は最低限以下を保証する。

5-1. 構造検査
JSON schema 一致
必須フィールド存在
型一致
enum 一致
5-2. 識別検査
task_id 一致
role 一致
cycle 一致
5-3. 工程ゲート検査

role ごとに、次工程へ進めるだけの最低限の中身があることを検査する。

これは帳票の様式検査だけでなく、
工程記録として最低限成立しているかの検査である。

6. role 定義
6-1. task_router
主責務
task の実行前整理
task_type の分類
risk_level の判断
各 role に必要な skill の選定
implementer が着手前に迷わないための初期注意点整理
必須出力
status
task_type
risk_level
role_skill_plan
used_skills
skill_selection_reason
initial_execution_notes
status
ready
blocked
禁止事項
自分で実装しない
reviewer 判断をしない
director 判断をしない
state.json を更新しない
実在しないファイルや仕様を断定しない
過剰な skill を付与しない
工程ゲート
used_skills に実際に使った固定 skill が記録されている
skill_selection_reason が空でない
initial_execution_notes が空でない
status=ready の場合、role_skill_plan が工程設計情報として成立している
6-2. implementer
主責務
実装 / 実行作業
実施内容の記録
懸念や未解決点の明示
必須出力
status
used_skills
summary
changed_files
commands_run
results
risks
questions
status
done
blocked
need_input
禁止事項
reviewer 判断をしない
director 判断をしない
state.json を更新しない
role や schema を変更しない
指示範囲を勝手に大きく広げない
Git 出荷責務を持たない
工程ゲート
summary が空でない
status=done の場合、少なくとも実施証跡が存在する
changed_files
commands_run
results
のいずれかが空でない
status=blocked / need_input の場合、停止理由または確認事項が読める
6-3. reviewer
主責務
implementer の結果検証
品質・妥当性・リスクの評価
director への判断材料整理
必須出力
decision
used_skills
summary
must_fix
nice_to_have
risks
decision
ok
needs_fix
blocked
禁止事項
自分で実装しない
director として最終判断しない
state.json を更新しない
role や schema を変更しない
工程ゲート
summary が空でない
decision=ok / needs_fix の場合、少なくとも以下のいずれかに根拠がある
must_fix
nice_to_have
risks
decision=blocked の場合、評価不能理由が summary または risks から読める
6-4. director
主責務
implementer / reviewer report をもとに最終判断する
approve / revise / stop を決定する
次アクションを整理する
必須出力
final_action
used_skills
summary
next_actions
remaining_risks
final_action
approve
revise
stop
禁止事項
自分で実装しない
reviewer として詳細レビューをやり直さない
state.json を更新しない
role や schema を変更しない
工程ゲート
summary が空でない
final_action=revise の場合、next_actions が空でない
final_action=stop の場合、停止理由が summary から読める
final_action=approve の場合、完了判断根拠が summary から読める
7. planner（補助 role）
7-1. 役割

completed task を入力に次 task 候補を提案する

7-2. 制約
実行 workflow に参加しない
state を変更しない
task を自動確定しない
実装を直接開始しない
7-3. 入力
completed task
docs
過去 report 群
task history
改善余地や未解決課題
project_config
development_mode
7-4. planner_type と development_mode

planner 系 role には少なくとも次の2軸がある。

planner_type
planner_safe
planner_improvement

これは提案の性格を表す。

development_mode
mainline
maintenance

これは現在の優先方針を表す。

7-5. development_mode の意味
mainline

主線を強く前進させる時期。

優先するもの:

主線機能の完成
end-to-end の貫通
主要フローの停滞解消
ユーザーが使える価値への接近
maintenance

保守・改善・安定化を優先する時期。

優先するもの:

低リスク改善
直前改善の補完
remaining_risks 回収
品質、運用性、判断精度の向上
7-6. planner_safe の方針
常に安全寄り proposal を出す
ただし mainline では「安全に主線を前進させる」ことを優先する
maintenance では低リスク改善、補完、安定化を優先する
7-7. planner_improvement の方針
常に改善 proposal を出す
mainline では将来価値のある改善資産として整理する
maintenance では採択候補として改善提案を積極評価してよい
8. plan_director（補助 role）
8-1. 役割

planner_safe / planner_improvement の proposal 群から、
次に実行する proposal を最大1件採択する。

8-2. 制約
task を自動確定しない
state.json を更新しない
複数採択しない
proposal 内容を推測で補わない
8-3. 入力
planner_safe_report
planner_improvement_report
proposal state
project_config
development_mode
source task / source reports
8-4. development_mode による採択方針
mainline
主線前進量を強く評価する
end-to-end の流れを完成に近づける proposal を強く評価する
改善継続を機械的に最優先しない
maintenance
低リスク改善、補完、安定化を強く評価する
改善 task 直後は改善継続 proposal を強く評価してよい
8-5. 改善 task 直後の扱い

source task が改善 task の場合でも、
改善継続を常に最優先にするわけではない。

maintenance では改善継続を強く優先してよい
mainline では主線前進量が高い proposal を優先してよい
9. 設計上の原則
9-1. role 分離
実装・評価・最終判断を分離する
1 role = 1 主責務を守る
9-2. 工程ゲート制御
各 role に進行条件を持たせる
validate が通らない限り advance しない
9-3. 証跡性
report に判断根拠を残す
docs / state / report で追跡可能にする
9-4. revise 時の再整理
修正は必ず task_router を通す
implementer に直接戻さない
9-5. AI より工程を賢くする
AI の能力依存を減らす
ルール、schema、validate、workflow に品質を持たせる
工場の品質管理のように、通過条件を明文化する
9-6. 提案の性格と現在方針を分離する
planner_type は提案の性格
development_mode は現在の優先方針

この分離により、
同じ proposal 基盤の上で主線推進期と保守改善期を切り替えられるようにする。

10. 将来拡張の前提
10-1. 標準作業ライン
task
↓
task_router
↓
implementer
↓
reviewer
↓
director
↓
release / git_operator
↓
completed
10-2. 改善提案ライン
completed task / issue
↓
planner
↓
proposal分類（safe / improvement / challenge）
↓
review / director
↓
採用案のみ task 化
↓
標準作業ラインへ投入

このとき planner / plan_director は development_mode を参照して、
今の時期に合う proposal と採択を行う。

10-3. 出荷ライン
director approve
↓
git_operator
↓
branch確認
↓
commit
↓
push
↓
必要なら PR 文面生成
10-4. GUI 連動

将来的には GUI から development_mode を切り替え、
proposal 生成と採択へ反映できるようにする。

11. 結論

本 workflow は、単なる AI 実行ツールではなく、
以下を備えた軽量な品質統制型の開発実行基盤を目指す。

規範層
実行層
証跡層
統制層
将来の出荷層

重視する思想は以下である。

標準作業で安定運用する
改善提案制度で攻めを管理する
出荷責務を専用 role に分離する
AI を賢くするより工程を賢くする
planner_type と development_mode を分離して運用方針を切り替える

これにより、

主線を強く押す時期
補完や改善を優先する時期

を同じ orchestrator 基盤の上で選択可能にする。
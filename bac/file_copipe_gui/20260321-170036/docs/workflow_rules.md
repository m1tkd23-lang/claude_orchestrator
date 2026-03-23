<!-- docs/workflow_rules.md -->
# claude_orchestrator ワークフロールール（rev2）

## 1. 目的

本書は、claude_orchestrator における以下を定義する。

- task 実行 workflow の状態遷移
- 各 role の責務 / 禁止事項
- report の必須要件
- validate 条件と工程ゲート
- revise / blocked / stop の扱い

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

8. 設計上の原則
8-1. role 分離

実装・評価・最終判断を分離する

1 role = 1 主責務を守る

8-2. 工程ゲート制御

各 role に進行条件を持たせる

validate が通らない限り advance しない

8-3. 証跡性

report に判断根拠を残す

docs / state / report で追跡可能にする

8-4. revise 時の再整理

修正は必ず task_router を通す

implementer に直接戻さない

8-5. AI より工程を賢くする

AI の能力依存を減らす

ルール、schema、validate、workflow に品質を持たせる

工場の品質管理のように、通過条件を明文化する

9. 将来拡張の前提
9-1. 標準作業ライン
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
9-2. 改善提案ライン
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
9-3. 出荷ライン
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
10. 結論

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
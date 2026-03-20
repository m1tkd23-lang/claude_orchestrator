# docs\workflow_rules.md
# claude_orchestrator ワークフロールール

## 1. 目的

本書は、claude_orchestrator におけるタスク処理の状態遷移、  
各 role の責務、skill の扱い、report の必須項目、および遷移条件を定義する。

Python（親アプリ）は本ルールに従って state を更新し、  
次に実行すべき role を決定する。

Claude は本ルールに従った JSON report を出力する。

---

## 2. 基本構造

1つの task は以下の流れで処理される。

`task_router → implementer → reviewer → director → (終了 or task_routerへ戻る)`

これを「1サイクル」と呼ぶ。  
director が `revise` を返した場合のみ、次サイクルへ進む。

### 2-1. task_router の位置づけ

task_router は、新規 task を実装開始前に整理するための最初の role である。

task_router は以下を行う。

- task_type を分類する
- risk_level を判断する
- 各 role に必要な skill を決める
- implementer 開始前の注意点を整理する

task_router は実装しない。  
task_router は reviewer / director を兼ねない。  
task_router は state.json を更新しない。

---

## 3. role と skill の関係

### 3-1. role とは何か

role は責任の単位である。

- task_router: task を整理し、skill を割り当てる
- implementer: 実装または実行作業を行う
- reviewer: implementer の結果を確認する
- director: 最終判断を行う
- planner: completed task をもとに次 task 候補を提案する（実行 workflow には含めない）

### 3-2. skill とは何か

skill は、各 role がどう進めるかを定義した作業手順である。

例:
- `route-task`
- `write-plan`
- `execute-plan`
- `code-review`

### 3-3. skill の配置

skill は `.claude_orchestrator\skills\<role>\` 配下に置く。

例:
- `.claude_orchestrator\skills\task_router\route-task.md`
- `.claude_orchestrator\skills\implementer\write-plan.md`
- `.claude_orchestrator\skills\implementer\execute-plan.md`
- `.claude_orchestrator\skills\reviewer\code-review.md`

### 3-4. skill の追加方針

skill は人が追加する。  
基本方針は以下とする。

- skill は人が作成する
- 必要に応じて Claude が skill 案を提案することはある
- 追加した skill は `route-task.md` の付与条件も更新する
- skill を置くだけでは自動で使われない
- task_router が `role_skill_plan` に含めて初めて運用に乗る

### 3-5. task_router と skill 配布

task_router は task の内容を読み、  
各 role に必要な skill を `role_skill_plan` として決定する。

skill は 1 role に対して複数付与できる。  
配列順は実行順を表す。

例:
```json
{
  "role_skill_plan": {
    "task_router": ["route-task"],
    "implementer": ["write-plan", "execute-plan"],
    "reviewer": ["code-review"],
    "director": []
  }
}
4. state の基本定義

state.json は以下を持つ。

{
  "task_id": "TASK-0001",
  "cycle": 1,
  "status": "in_progress",
  "current_stage": "task_router",
  "next_role": "task_router",
  "last_completed_role": null,
  "max_cycles": 3
}
フィールド説明

task_id: タスク識別子

cycle: 現在のサイクル番号

status: 全体状態

current_stage: 現在処理中の role

next_role: 次に実行すべき role

last_completed_role: 直前に完了した role

max_cycles: 最大ループ回数

5. task.json の基本方針

task.json には、通常の task 情報に加えて、task_router の判断結果を保存する。

主な保持項目:

task_type

risk_level

role_skill_plan

skill_selection_source

skill_selection_reason

initial_execution_notes

5-1. task_router 固定 skill

task 作成直後の初期値として、task.json の role_skill_plan.task_router には
["route-task"] を入れる。

6. 全体ステータス

status は以下のいずれか。

in_progress

completed

blocked

stopped

意味

in_progress: 処理中

completed: 正常終了

blocked: 外部要因や判断不能で停止

stopped: 意図的停止（director 判断または上限停止）

7. task_router ルール
出力 JSON の必須キー

task_id

role = "task_router"

cycle

status

task_type

risk_level

role_skill_plan

used_skills

skill_selection_reason

initial_execution_notes

status の値

ready

blocked

used_skills の扱い

task_router は固定 skill route-task を使う前提のため、
通常は used_skills = ["route-task"] とする。

遷移
task_router.status	次
ready	implementer
blocked	blocked終了
備考

task_router は実装前の整理専用 role

task_router の report は validate 後、advance 時に task.json へ反映される

director が revise を返した場合、次サイクルでも最初に task_router が動く

8. implementer ルール
出力 JSON の必須キー

task_id

role = "implementer"

cycle

status

used_skills

summary

status の値

done

blocked

need_input

used_skills の扱い

実際に使った skill 名だけを配列で記録する

割り当てられていても使っていない skill は入れない

割り当て skill が空なら used_skills は空配列でもよい

遷移
implementer.status	次
done	reviewer
blocked	blocked終了
need_input	blocked終了
備考

done の場合のみ reviewer に進む

blocked / need_input はその時点で停止扱い

9. reviewer ルール
出力 JSON の必須キー

task_id

role = "reviewer"

cycle

decision

used_skills

summary

decision の値

ok

needs_fix

blocked

used_skills の扱い

実際に使った skill 名だけを配列で記録する

割り当てられていても使っていない skill は入れない

割り当て skill が空なら used_skills は空配列でもよい

遷移
reviewer.decision	次
ok	director
needs_fix	director
blocked	blocked終了
備考

reviewer は原則として director に判断を委ねる（blocked除く）

10. director ルール
出力 JSON の必須キー

task_id

role = "director"

cycle

final_action

used_skills

summary

final_action の値

approve

revise

stop

used_skills の扱い

実際に使った skill 名だけを配列で記録する

割り当てられていても使っていない skill は入れない

割り当て skill が空なら used_skills は空配列でもよい

遷移
director.final_action	次
approve	completed
revise	task_router（cycle+1）
stop	stopped
備考

revise の場合のみ cycle をインクリメントする

approve でタスク終了

revise 後の再開点は implementer ではなく task_router

11. cycle 管理
初期値

cycle = 1

増加条件

director.final_action == revise

上限チェック

cycle > max_cycles の場合は status = stopped

意図

無限ループ防止

再サイクル時も task_router による再整理を入れる

12. 遷移フローチャート
[START]
   ↓
task_router
   ↓ (ready)
implementer
   ↓ (done)
reviewer
   ↓ (ok / needs_fix)
director
   ↓
 ┌───────────────┐
 │ approve       │→ completed
 │ revise        │→ task_router (cycle+1)
 │ stop          │→ stopped
 └───────────────┘
異常系

task_router(blocked) → blocked

implementer(blocked/need_input) → blocked

reviewer(blocked) → blocked

13. 異常系ルール
13-1. JSON不正

JSON parse失敗

schema不一致

→ status = blocked

13-2. task_id不一致

→ status = blocked

13-3. role不一致

→ status = blocked

13-4. cycle不一致

→ status = blocked

13-5. 必須キー欠落

→ status = blocked

14. Python の責務

Python は以下を行う。

report JSON の存在確認

schema 検証

フラグ抽出

state 更新

next_role 決定

task_router 結果の task.json 反映

Python は判断ロジックを持たず、
本ルールに従って機械的に遷移する。

15. Claude の責務

Claude は以下を行う。

自身の role に従った作業

割り当てられた skill を参照した作業

正しい JSON 出力

フラグの明示

used_skills の明示

Claude は以下を行わない。

state.json の更新

workflow 遷移の決定

role の変更

16. 現在の運用前提

本ワークフローは、GUI 上からの自動ループ実行を前提に扱う。

現在の代表的な手順

Python が prompt を生成する

GUI が Claude CLI を非対話実行する

Claude が report JSON を inbox に保存する

Python が validate する

Python が advance する

completed または停止条件まで自動で継続する

補足

手動の show-next / validate / advance はデバッグ・補助用途として残す

実行中の進行状況は GUI 上で確認可能

実行は非同期化されており、GUI を固めない構成である

17. task_router の判断基準

task_router の判断は、固定 skill route-task.md に従う。
判断の中心は以下である。

task の主目的

影響範囲

実装前整理が必要か

実行フェーズが必要か

通常レビューが必要か

現在の基本分類

新機能追加 → feature

不具合修正 → bugfix

構造整理 → refactor

文書更新中心 → docs

調査中心 → research

雑多な整備 → chore

現在の基本 skill 配布方針

implementer

実装前整理が必要 → write-plan

実装 / 実行本体が必要 → execute-plan

bugfix の原因切り分け中心 → debug-fix を検討

schema / migration 系 → migration-safety-check を検討

reviewer

原則 code-review

director

当面は空配列可

運用方針

skill は最小限にする

task を数件回して、想定とズレたら route-task.md の条件文を更新する

task_router 自体を育てる運用とする

18. planner との関係

planner は、completed task を入力に
次 task 候補を提案する補助 role である。

planner は以下を行わない。

実行 workflow への参加

skill の自動決定

task の自動確定

state 遷移の決定

つまり、

planner = 次 task 候補の提案者

task_router = 実行前の task 整理者 / skill 配布者

であり、役割は明確に分離される。

19. 設計原則

単純な状態遷移を保つ

role と skill を分離する

skill は人が追加する

task_router が skill を配る

Claude に曖昧な遷移判断をさせない

Python は厳密に検証する

無限ループを防ぐ

異常系は即停止

実際に使った skill は used_skills で残す

20. 現段階の結論

本ワークフローは以下を保証する。

task_router を含む役割分離された処理

JSON ベースの明確な状態遷移

skill 配布と skill 実使用記録

厳密な validate と advance

GUI からの非同期自動実行

completed までの安全な収束

本ルールを実装と運用の基準とする。
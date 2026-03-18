<!-- docs\workflow_rules.md -->
# claude_orchestrator ワークフロールール

## 1. 目的

本書は、claude_orchestrator におけるタスク処理の状態遷移、  
各役割の出力フラグ、および遷移条件を定義する。

Python（親アプリ）は本ルールに従って state を更新し、  
次に実行すべき role を決定する。

Claude は本ルールに従った JSON report を出力する。

---

## 2. 基本構造

1つの task は以下のサイクルで処理される。

`implementer → reviewer → director → (終了 or implementerへ戻る)`

これを「1サイクル」と呼ぶ。  
複数サイクルを繰り返すことでタスクを収束させる。

---

## 3. state の基本定義

state.json は以下を持つ。

```json
{
  "task_id": "TASK-0001",
  "cycle": 1,
  "status": "in_progress",
  "current_stage": "implementer",
  "next_role": "implementer",
  "last_completed_role": null,
  "max_cycles": 3
}
フィールド説明

task_id: タスク識別子

cycle: 現在のサイクル番号

status: 全体状態

current_stage: 現在処理中の役割

next_role: 次に実行すべき役割

last_completed_role: 直前に完了した役割

max_cycles: 最大ループ回数

4. 全体ステータス

status は以下のいずれか。

in_progress

completed

blocked

stopped

意味

in_progress: 処理中

completed: 正常終了

blocked: 外部要因で停止

stopped: 意図的停止（director 判断または上限停止）

5. implementer ルール
出力 JSON の必須キー

task_id

role = "implementer"

cycle

status

summary

status の値

done

blocked

need_input

遷移
implementer.status	次
done	reviewer
blocked	blocked終了
need_input	blocked終了
備考

done の場合のみ reviewer に進む

blocked / need_input はその時点で停止扱い

6. reviewer ルール
出力 JSON の必須キー

task_id

role = "reviewer"

cycle

decision

summary

decision の値

ok

needs_fix

blocked

遷移
reviewer.decision	次
ok	director
needs_fix	director
blocked	blocked終了
備考

reviewer は常に director に判断を委ねる（blocked除く）

7. director ルール
出力 JSON の必須キー

task_id

role = "director"

cycle

final_action

summary

final_action の値

approve

revise

stop

遷移
director.final_action	次
approve	completed
revise	implementer（cycle+1）
stop	stopped
備考

revise の場合のみ cycle をインクリメントする

approve でタスク終了

8. cycle 管理
初期値

cycle = 1

増加条件

director.final_action == revise

上限チェック

cycle > max_cycles の場合は status = stopped

意図

無限ループ防止

9. 遷移フローチャート
[START]
   ↓
implementer
   ↓ (done)
reviewer
   ↓ (ok / needs_fix)
director
   ↓
 ┌───────────────┐
 │ approve       │→ completed
 │ revise        │→ implementer (cycle+1)
 │ stop          │→ stopped
 └───────────────┘

異常系:

implementer(blocked/need_input) → blocked

reviewer(blocked) → blocked

10. 異常系ルール
10-1. JSON不正

JSON parse失敗

schema不一致

→ status = blocked

10-2. task_id不一致

→ status = blocked

10-3. role不一致

→ status = blocked

10-4. cycle不一致

→ status = blocked

10-5. 必須キー欠落

→ status = blocked

11. Python の責務

Python は以下を行う。

report JSON の存在確認

schema 検証

フラグ抽出

state 更新

next_role 決定

Python は判断ロジックを持たず、
本ルールに従って機械的に遷移する。

12. Claude の責務

Claude は以下を行う。

自身の role に従った作業

正しい JSON 出力

フラグの明示

Claude は以下を行わない。

state.json の更新

workflow 遷移の決定

role の変更

13. 現在の運用前提

本ワークフローは、初期段階の半自動運用から進み、
現在は GUI 上からの自動ループ実行 を前提に扱える。

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

14. 設計原則

単純な状態遷移を保つ

フラグは最小限にする

Claude に曖昧な判断をさせない

Python は厳密に検証する

無限ループを防ぐ

異常系は即停止

15. planner との関係

planner は今後追加予定の 次 task 候補提案ロール であり、
本書で定義する implementer / reviewer / director の実行ワークフローには含めない。

planner は completed task を入力に、次 task 候補を提案する補助ロールとして扱う。
planner は state 遷移を持たず、task 自体を自動確定しない。

16. 現段階の結論

本ワークフローは以下を保証する。

役割分離された処理

JSONベースの明確な状態遷移

厳密な validate と advance

GUI からの非同期自動実行

completed までの安全な収束

本ルールを実装の基準とする。
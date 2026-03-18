# docs\workflow_rules.md

# claude_orchestrator ワークフロールール

## 1. 目的

本書は、claude_orchestrator におけるタスク処理の状態遷移、
各役割の出力フラグ、および遷移条件を定義する。

Python（親アプリ）は本ルールに従って state を更新し、
次に実行すべき role を決定する。

Claude は本ルールに従った JSON report を出力する。


## 2. 基本構造

1つの task は以下のサイクルで処理される。
implementer → reviewer → director → (終了 or implementerへ戻る)


これを「1サイクル」と呼ぶ。

複数サイクルを繰り返すことでタスクを収束させる。


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

stopped: 意図的停止（director判断）

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
if cycle > max_cycles:
    status = stopped
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

13. 手動運用前提

本ワークフローは初期段階では半自動とする。

手順:

Python が prompt を生成

人が Claude Code に貼り付け

Claude が JSON を出力

JSON を inbox に保存

Python が advance コマンドで遷移

完全自動化は後段階で検討する。

14. 設計原則

単純な状態遷移を保つ

フラグは最小限にする

Claude に曖昧な判断をさせない

Python は厳密に検証する

無限ループを防ぐ

異常系は即停止

15. 現段階の結論

本ワークフローは以下を保証する。

役割分離された処理

JSONベースの明確な状態遷移

人手介入可能な安全設計

GUI拡張可能な構造

本ルールを実装の基準とする。
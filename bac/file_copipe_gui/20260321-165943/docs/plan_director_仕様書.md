# docs/plan_director_仕様書.md
# plan_director 仕様書

## 1. 目的

plan_director は planner により生成された proposal 群から、
次に実行する task を選定する最終判断ロールである。

- planner は「提案」を行う
- plan_director は「採択」を行う

この分離により、提案の自由度と実行の安全性を両立する。

---

## 2. 主責務

- proposal の評価
- スコアリング
- 採用候補の決定（最大1件）
- 不採用判断（全件不採用も可）
- task 自動生成可否の決定

---

## 3. 入力

- planner_safe_report
- planner_improvement_report（存在する場合）
- proposal_state（deferred / rejected 等）
- project_config

---

## 4. 出力（report）

### 4-1. 基本構造

```json
{
  "task_id": "TASK-0001",
  "role": "plan_director",
  "cycle": 1,
  "decision": "adopt | no_adopt",
  "selected_proposal_id": "proposal_0001 | null",
  "selection_reason": "string",
  "scores": [
    {
      "proposal_id": "proposal_0001",
      "score": 0.85,
      "reason": "string"
    }
  ]
}
5. decision の意味

adopt
→ proposal を1件採用し、次 task を生成する

no_adopt
→ 今回は次 task を生成しない

6. スコアリングルール
6-1. スコア範囲

0.0 ～ 1.0

6-2. 基本評価軸
項目	内容
安全性	既存機能を壊さないか
明確性	task が具体的か
依存関係	depends_on が満たされているか
優先度	priority（high/medium/low）
リスク	risk_level が低いか
7. 採択ルール
7-1. 最大1件

最もスコアの高い proposal を1件選ぶ

7-2. しきい値

スコア < 0.6 → 採用しない

max_score < threshold → no_adopt
8. proposal 状態との関係
state	扱い
accepted	評価対象
deferred	評価対象
rejected	除外
9. 自動 task 生成

decision = adopt の場合のみ実行

CreateTaskFromProposalUseCase を使用

proposal_state を "task_created" に更新

10. 禁止事項

自分で実装しない

複数 proposal を同時採用しない

推測でスコアを決めない（必ず理由を書く）

11. 将来拡張

スコアリングの重み調整

project_config に threshold 設定追加

safe / improvement の優先制御
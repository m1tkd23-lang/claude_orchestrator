# docs\plan_director_仕様書.md
# plan_director 仕様書

## 1. 目的

plan_director は planner により生成された proposal 群から、
次に実行する task を選定する最終判断ロールである。

- planner は「提案」を行う
- plan_director は「採択」を行う

この分離により、提案の自由度と実行の安全性を両立する。

また、plan_director は
**development_mode に応じて採択基準を切り替える**
役割も持つ。

これにより、

- 主線を強く前に進める時期
- 保守、改善、安定化を優先する時期

の違いを proposal 採択へ反映できるようにする。

---

## 2. 主責務

- proposal の評価
- スコアリング
- 採用候補の決定（最大1件）
- 不採用判断（全件不採用も可）
- task 自動生成可否の決定
- development_mode を踏まえた採択基準の切替

---

## 3. 入力

- planner_safe_report
- planner_improvement_report（存在する場合）
- proposal_state（deferred / rejected 等）
- project_config
- development_mode

---

## 4. development_mode

### 4-1. 値

- mainline
- maintenance

### 4-2. 意味

#### mainline

主線を強く前進させる時期。

優先するもの:

- 主線機能の完成
- end-to-end の貫通
- 現在止まっている主要フローの解消
- ユーザーが使える価値への接近

#### maintenance

保守・改善・安定化を優先する時期。

優先するもの:

- 低リスク改善
- remaining_risks 回収
- 直前改善の補完
- 品質、運用性、判断精度の向上

### 4-3. planner_type との違い

- planner_type は proposal の性格
  - safe
  - improvement
- development_mode は今の採択方針
  - mainline
  - maintenance

plan_director はこの2軸を分けて評価する。

---

## 5. 出力（report）

### 5-1. 基本構造

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
6. decision の意味
adopt

proposal を1件採用し、次 task を生成する

no_adopt

今回は次 task を生成しない

7. スコアリングルール
7-1. スコア範囲

0.0 ～ 1.0

7-2. 基本評価軸
項目	内容
安全性	既存機能を壊さないか
明確性	task が具体的か
依存関係	depends_on が満たされているか
優先度	priority（high/medium/low）
リスク	高リスクすぎないか
実装可能性	今の repo / docs / task 状況で着手可能か
ライン継続性	source task と自然接続しているか
development_mode 適合性	今の時期の方針に合っているか
7-3. development_mode ごとの追加評価
mainline

以下を強く加点する。

主線を前に進める
end-to-end の流れを完成に近づける
現在の主要フローの停滞要因を解消する
ユーザーが使える価値に近い
主線完成に向けた前進量が大きい

この場合、改善 proposal は評価してよいが、
改善継続を機械的に優先してはならない。

maintenance

以下を強く加点する。

直前改善の効果を補完する
remaining_risks / reviews / reports を回収しやすい
小さく安全に品質を上げられる
運用性、保守性、判断精度を改善できる
改善ラインを不自然に中断しない
8. 採択ルール
8-1. 最大1件

最もスコアの高い proposal を1件選ぶ

8-2. しきい値

スコア < 0.6 → 採用しない

max_score < threshold → no_adopt

9. proposal 状態との関係
state	扱い
accepted	評価対象
deferred	評価対象
proposed	評価対象
rejected	除外
task_created	原則再作成対象外
10. 改善 task 直後の扱い

source task が Orchestrator 改善 task の場合、
従来は改善継続を強めに優先していた。

v2 以降は、これを development_mode 依存 とする。

10-1. maintenance の場合

以下を強く評価する。

source task の改善内容の延長線上にあるか
remaining_risks / reports を回収しやすいか
直前改善の効果検証または補完になっているか
改善ラインを不自然に中断せずに済むか

この場合、改善 proposal が十分に安全・明確・実装可能であれば、
主線 proposal より優先してよい。

10-2. mainline の場合

改善継続は評価要素のひとつだが、絶対条件ではない。

以下のような主線 proposal は改善 proposal より優先してよい。

主線完成に向けた前進量が大きい
主要フローを直接通せるようにする
ユーザー価値に近い
より具体的で実装可能性が高い
改善継続より完成度向上の効果が明確に高い
11. 自動 task 生成
decision = adopt の場合のみ実行
CreateTaskFromProposalUseCase を使用
proposal_state を "task_created" に更新
12. 禁止事項
自分で実装しない
複数 proposal を同時採用しない
推測でスコアを決めない（必ず理由を書く）
development_mode を無視して機械的に改善継続または主線復帰を選ばない
source task が改善 task であることだけを理由に、常に改善 proposal を採択しない
mainline であることだけを理由に、安全性や明確性を無視して主線 proposal を採択しない
13. 将来拡張
スコアリングの重み調整
project_config に threshold 設定追加
safe / improvement の優先制御
GUI から development_mode 切替
report に development_mode を明示保存
主線前進量 / 改善継続価値の補助スコア追加
14. 設計方針

plan_director は、
単にスコア最大 proposal を採るだけでなく、
今の時期に何を前に進めるべきか を判断する役割を持つ。

そのため、次の2軸を明確に分離する。

proposal の性格
safe / improvement / challenge
現在の採択方針
mainline / maintenance

この分離により、

主線を強く押す時期
補完や改善を進める時期

を同じ proposal 基盤の上で切り替えられるようにする。
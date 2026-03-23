<!-- docs/GUI再設計_次工程指示書.md -->
# GUI再設計 次工程指示書

## 1. 目的

claude_orchestrator の GUI は、標準ラインと後工程ラインの半自動化まで到達した。  
次工程では、これを「使いやすく、状況が一目で分かる GUI」へ再設計する。

目的は以下。

- 実行状態を一枚で把握しやすくする
- role ごとの進行と report 要約を可視化する
- 現在の GUI コードをさらに整理・分割し、保守しやすくする
- 将来の自動承認・全自走化に耐える表示設計へ近づける

---

## 2. 現状の課題

現状 GUI は機能面ではかなり進んだが、表示面には以下の課題がある。

- 実行タブと詳細タブの情報が分散している
- 現在どの role が動いているかは分かるが、全体の流れが一枚で見えにくい
- role ごとの report 内容を横断比較しにくい
- planner / plan_director の結果と標準ラインの report が画面上でつながって見えにくい
- ファイル構成としても、main_window_* mixin が徐々に肥大化している

---

## 3. 次工程の基本方針

### 3-1. まずレイアウト設計を行う

いきなり見た目を作り始めるのではなく、  
まず GUI の責務分割とタブ構成を整理する。

### 3-2. 実行状況を一枚で見られる overview / pipeline タブを作る

新しいタブとして、実行全体を見渡せる画面を追加する。

### 3-3. role ごとの状態可視化を強める

標準ライン・後工程ラインの各 role をカード状またはパネル状に並べ、  
現在実行中の role が色や強調で分かるようにする。

### 3-4. report 要約を role ごとに並べる

最低限、以下の role の report 要約を画面上で見られるようにしたい。

- task_router
- implementer
- reviewer
- director
- planner
- plan_director

---

## 4. 目指す画面イメージ

新しい overview / pipeline タブのイメージは以下。

### 上段: 現在 task 情報

- task_id
- title
- status
- cycle
- next_role
- planner_role
- plan_director decision
- 停止予約状態

### 中段: role の進行可視化

role を横並び、または縦並びで配置する。

例:

```text
task_router | implementer | reviewer | director | planner | plan_director

表示ルール例:

未実行: グレー

完了: 緑

実行中: 青または強調色

blocked / stop: 赤系

承認待ち: 黄系

下段: role ごとの report 要約

各 role ごとに以下を表示できるとよい。

status / decision / final_action

summary

must_fix / risks / remaining_risks の要点

planner summary

plan_director selection_reason

必要なら「全文 JSON を表示」ボタンや、
「prompt / output path を開く」導線も検討する。

5. タブ再編の方向性

候補としては、以下のような構成が考えられる。

案A

実行

パイプライン

詳細

Remote Claude

案B

実行

概要

planner / proposal

詳細

Remote Claude

次工程では、どちらがよいかを比較しつつ、
最低でも「一枚で全体が見えるタブ」を1つ増やす方向で進めたい。

6. コード分割方針

現状でもタブファイル分割は始まっているが、
次工程ではさらに小さく分割する。

候補例:

gui/tabs/execution_tab.py

gui/tabs/detail_tab.py

gui/tabs/remote_tab.py

gui/tabs/pipeline_tab.py （新規）

さらに widget 単位へ分割することを検討する。

候補例:

gui/widgets/task_summary_panel.py

gui/widgets/pipeline_role_strip.py

gui/widgets/role_report_panel.py

gui/widgets/plan_director_panel.py

gui/widgets/planner_proposal_panel.py

7. 次工程でまず行うべき作業
Step 1

現行 GUI の責務整理メモを作る

最低限まとめたい内容:

各タブの役割

各 mixin の役割

どの処理がどこにあるか

どこが肥大化しているか

Step 2

新しい overview / pipeline タブのレイアウト案を作る

情報配置案

role 表示案

report 要約案

色分け方針

Step 3

widget 分割方針を決める

タブ単位

パネル単位

role strip 単位

Step 4

その後に実装へ入る

8. 実装時の注意

既存機能を壊さないこと

まず表示整理を優先し、後から細かい操作改善を足すこと

planner / plan_director / waiting approval を overview 側でも見えるようにすること

JSON 全文より、まずは summary / decision / status の要点表示を優先すること

将来の自動承認化を見据え、承認待ち状態が視覚的に分かる設計にすること

9. 次工程のゴール

次工程の完了条件は以下。

GUI の全体状況が一枚で分かるタブが追加されている

実行中 role が視覚的に分かる

role ごとの report 要約が見える

既存フロー（標準ライン + planner + plan_director + 承認 + 次task自動実行）を壊さない

GUI コードが今より分割され、今後の改善をしやすい状態になっている

10. 次に着手する具体作業

次の会話では、まず以下に進むのが自然。

現行 GUI の責務分解

overview / pipeline タブの画面設計

widget 分割案

その後、実装用ファイル分割と新タブ実装
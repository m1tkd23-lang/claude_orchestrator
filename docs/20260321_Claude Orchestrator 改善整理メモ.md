Claude Orchestrator 改善整理メモ

テーマ: 配線ルールと接続順の最適化

1. 現状評価

Claude Orchestrator は、すでに以下の土台を持っている。

role 分離が明確
prompt template がある
schema による最低限の品質担保がある
report 保存先の統制がある
実運用でも TASK-0001〜0003 は大きく破綻していない

したがって現状は、
「土台不足」ではなく「受け渡しルールと接続順の最適化段階」
と評価できる。

2. 良い点
2-1. role 責務分離が明確
task_router: task整理
implementer: 実装
reviewer: 評価
director: 最終判断

責務の混線が起きにくい。

2-2. prompt template が実務的

各 role に対して、

入力
出力
保存先
禁止事項
品質条件

がかなり具体的に与えられている。

2-3. schema による最低限の品質担保
summary 必須
used_skills 記録
changed_files / commands_run / results
must_fix / nice_to_have / risks
remaining_risks

など、証跡と判断理由を残す枠組みがある。

2-4. 実運用でも流れは健全

TASK-0001〜0003を見る限り、

スコープ逸脱が少ない
レビュー結果が次タスクに流れている
director が残課題を残している

という点で、流れは機能している。

3. 現状の主要課題
3-1. constraints 同士の整合チェックが弱い

もっとも大きい課題。
TASK-0003 では、

開発依存を requirements-dev.txt に分離
requirements.txt だけでテスト実行可能

という、実質両立しにくい条件が同居した。

これは implementer の問題ではなく、
task生成時の整合チェック不足 によるもの。

3-2. 残課題の引き継ぎが仕組み化されていない

現状でも remaining_risks や risks は機能しているが、

次タスクが必ず拾う
reviewer / director が必ず参照する

という仕組みにはなっていない。

今は「うまく読めば流れる」状態であり、
明示的な carry-over 構造が不足している。

3-3. write-plan の出力先が曖昧

write-plan を使った場合に、

どこへ保存するか
implementer_report でどう参照するか

が固定されていない。

このため、計画が「実際に残ったのか」「どこにあるのか」が見えにくい。

3-4. 未確定事項と確定事項の区別が弱い

現状の task / report では、

確定した方針
仮置き前提
要確認事項

が文章の中に混在しやすい。

このため、後続タスクで

仮置きが確定扱いされる
未確定事項が暗黙に固定される

リスクがある。

3-5. director の判断粒度が粗い

approve / revise / stop の3値はシンプルだが、

approve だが注意点が多い
通してよいが条件付き
次タスク前に確認前提

といった温度差を表現しにくい。

3-6. reviewer / director の前段整合確認が弱い

現状でも実務上は見ているが、prompt / schema 上は

前タスクの remaining_risks
why_now に書いた引継ぎ理由
直前 director の未解決事項

を必ず確認する構造にはなっていない。

4. 改善方針

改善方針は次の4本柱で整理できる。

方針A: task生成時の整合性を強化する

task_router が task を作る段階で、

constraints の矛盾
scope の過不足
実行可能性
を点検する。
方針B: 残課題の引き継ぎを構造化する

remaining_risks を単なる記録で終わらせず、
次タスクに明示的に渡す。

方針C: 計画と判断の証跡を見える化する

write-plan や方針決定結果の保存先・参照先を固定する。

方針D: 未確定事項の扱いを明文化する

仮定・確定・要確認を区別して、後続誤読を減らす。

5. 優先度付き改善案
優先度A（先にやるべき）
A-1. task_router に constraints 矛盾チェックを追加

task_router.md と task_router_prompt.txt に明記する。

追加したい観点:

constraints 同士に矛盾がないか
完了条件と制約が衝突していないか
dev依存分離と単独実行条件が両立しているか
未確定事項を前提固定していないか
A-2. 次タスクへの引継ぎ欄を追加

task.schema.json または運用ルールに、たとえば以下を追加。

carry_over_risks
must_consider_from_previous_task
open_decisions

これにより、次タスク生成時に前タスクの残課題を強制参照できる。

A-3. write-plan の出力先固定

例:

.claude_orchestrator/tasks/TASK-xxxx/plan.md

さらに implementer_report に

plan_artifacts
または
planning_notes_path
を追加すると追跡しやすい。
優先度B（次にやるべき）
B-1. assumptions / confirmed_decisions の分離

task.json または設計文書に以下のような区分を持たせる。

confirmed_decisions
assumptions
needs_confirmation

これで、未確定事項の固定化を防ぎやすくなる。

B-2. reviewer / director に前段参照の明示追加

prompt に以下を追加する。

前タスクから引き継いだ remaining_risks を確認すること
why_now で言及された引継ぎ理由を確認すること
前サイクル / 前タスクの未解決事項との整合を確認すること
B-3. director 承認粒度の拡張検討

たとえば将来的に

approve
approve_with_notes
revise
stop

なども検討余地あり。

ただしこれは schema や workflow 側にも影響するため、優先度はAより下。

優先度C（中長期でよい）
C-1. report schema の構造強化

将来的に以下の拡張を検討。

decision_basis
carry_over_risks
resolved_risks
referenced_previous_reports
C-2. docs / task_maps との接続強化

運用ルール側に、

remaining_risks の引継ぎ方法
blocked にすべき条件
未確定事項の扱い
を明記する。
6. 具体的な改善対象ファイル

優先度Aの改善対象候補は以下。

.claude_orchestrator/roles/task_router.md
.claude_orchestrator/templates/task_router_prompt.txt
.claude_orchestrator/templates/implementer_prompt.txt
.claude_orchestrator/templates/reviewer_prompt.txt
.claude_orchestrator/templates/director_prompt.txt
.claude_orchestrator/schemas/task.schema.json
.claude_orchestrator/schemas/implementer_report.schema.json
.claude_orchestrator/schemas/director_report.schema.json

加えて、運用ルール整理用として

.claude_orchestrator/docs/project_core/開発の目的本筋.md
.claude_orchestrator/docs/task_maps/TASKフロー全体図.md
.claude_orchestrator/docs/task_maps/role別最小参照マップ.md

も更新候補になりうる。

7. まず着手すべき順番

推奨順はこれです。

task_router の整合チェック強化
carry-over ルールの追加
write-plan 出力先の固定
assumptions / confirmed_decisions の分離
reviewer / director の前段参照強化
director 承認粒度の再設計
8. 良い点まとめ
器はできている
role分離は明確
template は実用的
schema は最低限十分強い
実運用でも破綻していない
根本作り直しではなく改善で伸ばせる状態
9. 改善点まとめ
task定義時の矛盾検出が弱い
残課題の引継ぎが明文化されていない
write-plan の証跡が見えにくい
未確定事項が暗黙固定されやすい
director の判断粒度が粗い
reviewer / director の前段整合確認が弱い
10. 最後のまとめ

Claude Orchestrator は、
「賢い処理を行わせるための器と配線」はすでに持っている。

次にやるべきことは、
配線ルールと接続順を最適化すること であり、その中心は次の3点です。

task生成時の整合性強化
残課題の引継ぎ構造化
計画と判断の証跡の見える化

この方向で進めれば、今の土台を活かしたまま、かなり強い Orchestrator に近づけます。
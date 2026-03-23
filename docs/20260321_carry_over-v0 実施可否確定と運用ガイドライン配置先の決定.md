TASK案
タイトル

carry_over-v0 実施可否確定と運用ガイドライン配置先の決定

description

Claude Orchestrator における carry_over-v0（最小導入案）の実施可否を確定し、
実装前に必要な運用ルールと配置先を明文化する。

TASK-0011 で整理した carry_over 設計メモでは、

remaining_risks を中心とした引き継ぎ
prompt 変更ベースの最小導入（carry_over-v0）

が提案されているが、以下が未確定のまま残っている。

task_router_prompt.txt の変更が constraints に抵触するかどうか
carry_over 運用ガイドラインの配置先（docs / roles / tasks / README など）

本 task では実装に進まず、以下を明確にする。

1. task_router_prompt.txt 変更の可否判定
task_router_prompt.txt が「workflow 本体」に該当するかどうかを判断する
constraints（既存 workflow / schema / Python 実装を変更しない）との整合を確認する
変更が許容される場合／されない場合の根拠を明記する
2. carry_over-v0 運用ガイドラインの設計

以下を定義する。

carry_over 対象（remaining_risks を中心とする）
次 task への受け渡し方法
context_files に前 task director_report を含めるルール
initial_execution_notes への記載ルール
最低限の記述フォーマット（例：プレフィックス形式の案）
3. ガイドラインの配置先決定

候補例：

.claude_orchestrator/docs/
.claude_orchestrator/roles/
.claude_orchestrator/templates/
repo ルート README

これらの中から、

参照されやすさ
role / prompt との整合
将来拡張性

の観点で最適な配置先を決定する。

4. carry_over-v0 の go / no-go 判断

以下を明示する。

carry_over-v0 を次 task で実装してよいか（go / no-go）
no-go の場合の理由
保留の場合の追加検討事項
成果物

以下の設計メモを作成する。

.claude_orchestrator/tasks/TASK-XXXX/ 配下に保存

内容：

可否判定結果
判断根拠
運用ガイドライン案
配置先決定
go / no-go 判断
未確定事項（あれば）
why_now

TASK-0011 により carry_over の設計は整理されたが、
実装に進むための前提条件（prompt変更の可否・ガイドライン配置先）が未確定のまま残っている。

この状態で実装に進むと、

constraints 違反の可能性
ガイドライン不在による運用崩壊

が発生するため、実装前に判断を確定させる必要がある。

context_files
.claude_orchestrator/tasks/TASK-0011/carry_over_design_memo.md
.claude_orchestrator/tasks/TASK-0011/inbox/director_report_v1.json
.claude_orchestrator/tasks/TASK-0011/inbox/reviewer_report_v1.json
.claude_orchestrator/templates/task_router_prompt.txt
.claude_orchestrator/roles/task_router.md
.claude_orchestrator/docs/project_core/開発の目的本筋.md
constraints
Python 実装は禁止
schema 変更は禁止
既存 role / template ファイルの直接変更は禁止
成果物は設計メモのみとする
判断は docs / role 定義 / 既存構造を根拠に行うこと
不明点は断定せず、仮案と要確認事項を分けること
carry_over-v0 の範囲を超える設計（v1/v2）は扱わないこと
depends_on
TASK-0011
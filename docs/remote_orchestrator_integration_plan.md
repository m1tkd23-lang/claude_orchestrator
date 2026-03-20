# docs\remote_orchestrator_integration_plan.md
# Remote Orchestrator Integration Plan (v1)

## 1. 目的

Claude Orchestrator GUI の既存機能を維持しつつ、Remote Claude Code から同一リポジトリを操作可能にする。

本計画で遠隔から実行可能にしたい対象は以下とする。

- タスク一覧確認
- planner 実行
- proposal 一覧確認
- proposal から task 作成
- task 実行

---

## 2. 背景

現在の Claude Orchestrator GUI は、対象 repo 配下の `.claude_orchestrator` フォルダを基盤として動作している。

GUI は主に以下を行っている。

- `.claude_orchestrator/tasks/...` の task / state / report を参照する
- role ごとの prompt を生成する
- `claude -p` を用いて Claude Code を非対話実行する
- report JSON を validate し、advance で state を更新する
- completed task に対して planner を実行し、proposal を扱う

このため、Remote 側も GUI を直接操作するのではなく、同じ `.claude_orchestrator` 配下を共有データ基盤として操作すれば連携可能である。

---

## 3. 基本方針

### 3-1. GUI と Remote は直接通信しない

GUI と Remote Claude は直接連携しない。  
両者は同一 repo の `.claude_orchestrator` を共有し、同じ UseCase / CLI 基盤を使って操作する。

共有対象の基盤は以下とする。

```text
<target_repo>\.claude_orchestrator\

この配下の JSON / TXT / planner 情報を唯一の正とする。

3-2. 既存 GUI の処理は維持する

既存 GUI の以下の処理は維持する。

repo 選択

task 一覧表示

show-next

validate-report

advance

auto run

planner 実行

proposal 表示と採否操作

3-3. Remote Claude は別セッションで並行起動する

Remote Claude は、GUI が使っている claude -p の一発実行とは別に、並行起動した Claude Code セッションとして扱う。

Remote Claude は GUI を直接触らず、CLI 経由で orchestrator を操作する。

3-4. GUI 専用操作は CLI / UseCase に寄せる

現在 GUI 内部に閉じている操作は、Remote Claude 側からも同じ処理ができるように UseCase / CLI へ寄せる。

4. 現状整理
4-1. 現在の Claude 実行方式

現状の claude_runner.py は以下の方式である。

claude -p

--permission-mode bypassPermissions

stdin で prompt を投入

実行終了まで待機

この方式は非対話・都度起動型である。
そのため、GUI 側の現在の Claude 実行セッションをそのまま Remote Control 対象にする構成は取らない。

4-2. 現在の auto run の構造

AutoRunWorker は概ね以下の流れで task を進めている。

show-next

prompt 読込

Claude 実行

report JSON 存在確認

validate-report

advance

completed または停止条件まで繰り返す

このロジックは GUI 内に寄っているため、Remote Claude 側からも同じ実行を可能にするには、共通 UseCase 化が必要である。

4-3. planner の現状

planner は既に以下の実装が存在する。

GenerateNextTaskProposalsUseCase

PlannerRuntime

PlannerWorker

ProposalStateStore

completed task を元に planner report を生成し、proposal を扱う導線はすでに存在する。

不足しているのは以下である。

CLI から planner を実行する入口

proposal 一覧を CLI で確認する入口

proposal から直接 task を作成する入口

task を CLI から auto run する入口

5. v1 の実装スコープ

v1 では以下を実装対象とする。

5-1. CLI 拡張

以下の新規コマンドを追加する。

generate-next-tasks

list-proposals

create-task-from-proposal

run-task

5-2. 共通 UseCase 追加

以下の UseCase を追加する。

RunTaskUseCase

ListProposalsUseCase

CreateTaskFromProposalUseCase

5-3. Remote セッション情報管理

GUI 上から Remote Claude 接続ボタンを押したときの状態を保持するため、Remote セッション情報管理を追加する。

5-4. GUI 追加

GUI に以下を追加する。

Remote Claude 接続ボタン

Remote 状態表示

Remote セッション名表示

6. v1 非スコープ

v1 では以下を対象外とする。

GUI 自体の遠隔操作

GUI ボタンの直接リモート操作

GUI と Remote のリアルタイム双方向同期

ファイル監視による即時更新

同一 Claude 実行セッションの共有

現在の claude -p 実行を Remote Control セッション化すること

7. データ共有モデル
7-1. 共有データの原則

GUI と Remote Claude は以下の同一 repo を対象とする。

例:

D:\Develop\claude_test_repo_rev3

両者とも以下を読み書きする。

D:\Develop\claude_test_repo_rev3\.claude_orchestrator\

この共有モデルにより、Remote 側が task / planner / proposal を操作した結果を GUI が後から読み込めるようにする。

7-2. 共有される主要ファイル

代表的な共有対象は以下とする。

task.json

state.json

outbox\*_prompt_v*.txt

inbox\*_report_v*.json

planner\planner_prompt_v*.txt

planner\planner_report_v*.json

planner\proposal_states_v*.json

7-3. Remote セッション情報の保存先

Remote 接続状態の保存先は以下とする。

<target_repo>\.claude_orchestrator\runtime\remote_session.json
8. 追加 UseCase 設計
8-1. RunTaskUseCase
目的

GUI の AutoRunWorker に寄っている task 自動進行ロジックを、CLI からも呼べる共通基盤にする。

責務

show-next

prompt 読込

Claude 実行

report 存在確認

validate-report

advance

completed / blocked / stopped / none までループ

想定入出力

入力:

repo_path

task_id

出力:

task_id

final status

final cycle

実行ログ

最終 state

実装方針

既存 AutoRunWorker._run_single_cycle_step() の処理を整理し、UseCase 側へ寄せる。
GUI はその UseCase を呼び、CLI も同じ UseCase を呼ぶ。

8-2. ListProposalsUseCase
目的

planner report と proposal state をまとめて読み込み、CLI や GUI から proposal 一覧を扱いやすくする。

責務

対象 task の planner report 読込

proposal_states 読込

proposal ごとの状態付与

一覧整形

想定入出力

入力:

repo_path

source_task_id

出力:

source_task_id

cycle

summary

proposals

proposal_id

title

description

state

why_now

depends_on

context_files

constraints

8-3. CreateTaskFromProposalUseCase
目的

proposal を task 作成フォームへ転記するだけでなく、直接 task として正式作成する。

責務

planner report 読込

proposal 抽出

proposal → task 作成用フィールド変換

CreateTaskUseCase 呼び出し

proposal state の accepted 更新

想定入出力

入力:

repo_path

source_task_id

proposal_id

出力:

source_task_id

proposal_id

created_task_id

created_task_dir

9. CLI 拡張仕様
9-1. generate-next-tasks
目的

completed task から planner を CLI で実行する。

例
python -m claude_orchestrator.cli.main generate-next-tasks --repo "D:\Develop\claude_test_repo_rev3" --task-id "TASK-0010"
出力例の方針

source_task_id

cycle

planner report path

proposal 件数

9-2. list-proposals
目的

planner report と proposal_states を読み、proposal 一覧を CLI で確認できるようにする。

例
python -m claude_orchestrator.cli.main list-proposals --repo "D:\Develop\claude_test_repo_rev3" --task-id "TASK-0010"
出力例の方針

proposal ごとに以下を表示する。

proposal_id

state

title

why_now

depends_on

9-3. create-task-from-proposal
目的

proposal から直接 task を作成する。

例
python -m claude_orchestrator.cli.main create-task-from-proposal --repo "D:\Develop\claude_test_repo_rev3" --task-id "TASK-0010" --proposal-id "P-001"
出力例の方針

source_task_id

proposal_id

created_task_id

created_task_dir

9-4. run-task
目的

指定 task を GUI の auto run 相当で completed / 停止まで実行する。

例
python -m claude_orchestrator.cli.main run-task --repo "D:\Develop\claude_test_repo_rev3" --task-id "TASK-0011"
出力例の方針

task_id

final status

final cycle

10. Remote セッション管理設計
10-1. 目的

GUI から Remote Claude 接続を開始したことを記録し、対象 repo ごとの接続状態を把握できるようにする。

10-2. 保存先
<target_repo>\.claude_orchestrator\runtime\remote_session.json
10-3. 格納フォーマット案
{
  "repo_path": "D:/Develop/claude_test_repo_rev3",
  "session_name": "orchestrator-remote",
  "status": "running",
  "mode": "remote-control",
  "last_started_at": "2026-03-19T10:00:00"
}
10-4. v1 の役割

v1 では以下のみを担う。

GUI 上で接続情報を表示する

Remote Claude 接続起動時に状態を保存する

最後に起動した session 名を記録する

v1 では、外部からセッション生存確認を厳密に行うところまでは実装対象外とする。

11. GUI 拡張設計
11-1. 追加 UI

Execution タブに以下を追加する。

Remote Claude 接続ボタン

Remote 状態表示

Remote セッション名表示

11-2. 想定挙動

Remote Claude 接続ボタン押下時:

GUI で選択中の repo_path を取得

Remote 用 Claude 起動コマンドを実行

remote_session.json を更新

GUI 上の状態表示を更新

11-3. v1 の位置づけ

このボタンは「Remote Claude オペレーター起動導線」とする。
GUI 自身を遠隔操作するものではない。

12. 排他ルール

v1 では以下を運用ルールとして明記する。

12-1. 同一 task の二重操作禁止

同じ task を GUI と Remote Claude の両方から同時に操作しない。

12-2. auto run 中 task の Remote 操作禁止

GUI で auto run 中の task に対して、Remote 側から planner / advance / run-task を行わない。

12-3. 共有 repo の統一

GUI と Remote Claude は必ず同じ repo_path を対象にする。

13. 実装順序
Step 1

RunTaskUseCase を追加する。
既存 GUI の auto run ロジックの中核を共通化する。

対象候補

新規: src\claude_orchestrator\application\usecases\run_task_usecase.py

更新: src\claude_orchestrator\gui\auto_run_worker.py

Step 2

CLI を拡張する。

追加コマンド

generate-next-tasks

list-proposals

create-task-from-proposal

run-task

対象候補

更新: src\claude_orchestrator\cli\main.py

Step 3

proposal 系 UseCase を追加する。

対象候補

新規: src\claude_orchestrator\application\usecases\list_proposals_usecase.py

新規: src\claude_orchestrator\application\usecases\create_task_from_proposal_usecase.py

Step 4

Remote セッション情報保存を追加する。

対象候補

新規: src\claude_orchestrator\infrastructure\remote_session_store.py

更新: src\claude_orchestrator\infrastructure\project_paths.py

Step 5

GUI を拡張する。

対象候補

更新: src\claude_orchestrator\gui\ui_sections.py

更新: src\claude_orchestrator\gui\main_window.py

更新: src\claude_orchestrator\gui\claude_runner.py

14. 成功条件

以下を満たせば v1 完了とする。

GUI の既存 auto run が壊れていない

Remote Claude から CLI で task 一覧確認ができる

Remote Claude から planner 実行ができる

Remote Claude から proposal 一覧確認ができる

Remote Claude から proposal から task 作成ができる

Remote Claude から task 実行ができる

GUI が .claude_orchestrator の更新内容を再読込して扱える

15. 今後の拡張候補

v1 完了後の拡張候補は以下とする。

通知機能

GUI の定期再読込

file watcher による状態追従

Remote 接続状態の詳細監視

GUI と Remote の協調ロック

複数 Remote セッション管理

Claude Code Remote Control のさらに深い統合

16. 現段階の結論

本計画では、既存 GUI の処理を残したまま、Remote Claude を別セッションで並行起動し、同じ .claude_orchestrator を共有して操作する構成を採る。

この構成により、以下を無理なく両立させる。

既存 GUI の安定運用

遠隔からの task / planner / proposal / run 操作

GUI と Remote の同一データ基盤による連携

本計画書を v1 実装の基準とする。
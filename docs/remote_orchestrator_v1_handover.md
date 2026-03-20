# docs\remote_orchestrator_v1_handover.md
# Remote Orchestrator v1 引き継ぎ資料

## 1. 本資料の目的

本資料は、Claude Orchestrator GUI に対して実装した Remote 連携 v1 の内容を整理し、今後の保守・改善・運用判断をしやすくするための引き継ぎ資料である。

本資料では以下を明確にする。

- v1 で実装した範囲
- できるようになった操作
- GUI と Remote Claude の関係
- 追加された CLI / UseCase / GUI の役割
- 現時点の制約と注意点
- 次工程候補

---

## 2. 結論

Remote Orchestrator v1 では、既存 GUI の処理内容を維持したまま、別セッションで起動した Remote Claude から同一 repo の `.claude_orchestrator` を共有基盤として操作できる状態になった。

これにより、以下の流れを GUI / CLI の両方で扱えるようになった。

- completed task から planner を実行
- proposal 一覧を確認
- proposal から task を作成
- task を実行

特に重要なのは、GUI と Remote Claude が直接通信するのではなく、同一 repo 配下の `.claude_orchestrator` を共有して動く構成に整理できたことである。

---

## 3. 採用した構成

## 3-1. 基本構造

本実装では、以下の構成を採用した。

- GUI  
  - 既存のローカル運用席
  - task 一覧・状態確認・auto run・planner 実行・proposal 表示を担当

- Remote Claude  
  - 別セッションで起動する遠隔オペレーター
  - GUI を直接操作せず、CLI を通して orchestrator を操作する

- 共有基盤  
  - `<repo>\.claude_orchestrator\`
  - task / state / report / planner / runtime のファイル群を唯一の正として扱う

## 3-2. 共有 repo の前提

GUI と Remote Claude は必ず同じ repo を対象とする。

例:

```text
D:\Develop\repos\claude_orchestrator

共有対象の基盤は以下である。

D:\Develop\repos\claude_orchestrator\.claude_orchestrator\
4. v1 で実装したもの
4-1. RunTaskUseCase 追加

GUI の AutoRunWorker に寄っていた task 自動進行ロジックを RunTaskUseCase に切り出した。

これにより、以下を GUI / CLI 共通で扱えるようになった。

show-next

Claude 実行

validate-report

advance

completed / stopped / blocked までのループ

4-2. CLI 拡張

以下の CLI コマンドを追加した。

run-task

generate-next-tasks

list-proposals

create-task-from-proposal

これにより、Remote Claude 側からも GUI と同じ基盤を使って planner / proposal / task 実行を行えるようになった。

4-3. proposal 系 UseCase 追加

以下を追加した。

ListProposalsUseCase

CreateTaskFromProposalUseCase

役割は以下の通り。

ListProposalsUseCase

planner report を読む

proposal_states を読む

proposal ごとの state を付与する

CLI / GUI から扱いやすい proposal 一覧を返す

CreateTaskFromProposalUseCase

planner report から proposal を抽出する

proposal を task 作成用フィールドへ変換する

CreateTaskUseCase を呼ぶ

proposal_state を accepted に更新する

4-4. Remote セッション状態保存追加

以下を追加した。

RemoteSessionStore

ProjectPaths.remote_session_path

保存先は以下である。

<repo>\.claude_orchestrator\runtime\remote_session.json

このファイルにより、GUI 上で Remote Claude の起動状態を表示できるようにした。

4-5. GUI 拡張

Execution タブに以下を追加した。

Remote Claude 接続ボタン

Remote 状態表示

Remote セッション名表示

状態再読込ボタン

また planner proposal エリアに以下を追加した。

task を直接作成 ボタン

これにより GUI 側でも proposal から正式に task を生成できるようになった。

5. 実際に確認できたこと

本実装後、以下を実際に確認済みである。

5-1. Remote セッション状態保存

GUI で Remote Claude 接続 ボタン押下後、以下が確認できた。

remote_session.json が作成される

status = running

session_name が保存される

last_started_at が保存される

GUI 上の Remote 表示が更新される

確認済み内容の例:

{
  "repo_path": "D:\\Develop\\repos\\claude_orchestrator",
  "session_name": "orchestrator-remote-claude_orchestrator",
  "status": "running",
  "mode": "remote-control",
  "last_started_at": "2026-03-19T10:32:53",
  "last_updated_at": "2026-03-19T10:32:53"
}
5-2. CLI による proposal 一覧取得

以下コマンドが正常動作することを確認済み。

python -m claude_orchestrator.cli.main list-proposals --repo "D:\Develop\repos\claude_orchestrator" --task-id TASK-0010

proposal 一覧・state・why_now・depends_on が取得できている。

5-3. CLI による proposal から task 作成

以下コマンドが正常動作することを確認済み。

python -m claude_orchestrator.cli.main create-task-from-proposal --repo "D:\Develop\repos\claude_orchestrator" --task-id TASK-0010 --proposal-id PLAN-0001

実際に TASK-0014 が作成されたことを確認している。

5-4. CLI による run-task

以下コマンドが正常動作することを確認済み。

python -m claude_orchestrator.cli.main run-task --repo "D:\Develop\repos\claude_orchestrator" --task-id TASK-0011

task が completed まで進むことを確認済み。

5-5. GUI から proposal 直接 task 化

GUI 上で以下の流れが正常動作することを確認済み。

completed task を選択

次タスク案作成

proposal を選択

task を直接作成

実際に TASK-0015 が作成されたことを確認している。

6. 使い方
6-1. GUI 側の使い方
Remote Claude 起動

GUI で対象 repo を選択する

Remote Claude 接続 を押す

GUI の Remote 表示を確認する

必要に応じて 状態再読込 を押す

planner から task 作成

completed task を選択する

次タスク案作成 を押す

proposal を選択する

task を直接作成 を押す

新しい task が task 一覧に追加される

従来どおりの運用

以下は従来どおり GUI から操作可能である。

task 作成

show-next

validate-report

advance

Claude 実行(自動完了まで)

planner 実行

proposal の採用 / 否決 / 保留

6-2. Remote Claude 側の使い方

Remote Claude は GUI を直接操作しない。
Remote Claude は、同じ repo 上で CLI を実行するオペレーターとして使う。

task 一覧確認
python -m claude_orchestrator.cli.main status --repo "D:\Develop\repos\claude_orchestrator"
planner 実行
python -m claude_orchestrator.cli.main generate-next-tasks --repo "D:\Develop\repos\claude_orchestrator" --task-id TASK-0010
proposal 一覧確認
python -m claude_orchestrator.cli.main list-proposals --repo "D:\Develop\repos\claude_orchestrator" --task-id TASK-0010
proposal から task 作成
python -m claude_orchestrator.cli.main create-task-from-proposal --repo "D:\Develop\repos\claude_orchestrator" --task-id TASK-0010 --proposal-id PLAN-0001
task 実行
python -m claude_orchestrator.cli.main run-task --repo "D:\Develop\repos\claude_orchestrator" --task-id TASK-0014
7. proposal_id に関する注意

planner report の proposal_id は、現状 PLAN-0001 のような形式で出力されている。

そのため、create-task-from-proposal を使う際は、実際の proposal_id を list-proposals で確認したうえで指定すること。

例:

正しい例: PLAN-0001

誤り例: P-001

本実装中に、P-001 指定で Proposal not found が発生したが、これは実装不良ではなく proposal_id 不一致によるものであった。

8. 追加・更新された主なファイル
8-1. 新規追加

src\claude_orchestrator\application\usecases\run_task_usecase.py

src\claude_orchestrator\application\usecases\list_proposals_usecase.py

src\claude_orchestrator\application\usecases\create_task_from_proposal_usecase.py

src\claude_orchestrator\infrastructure\remote_session_store.py

docs\remote_orchestrator_integration_plan.md

8-2. 更新

src\claude_orchestrator\cli\main.py

src\claude_orchestrator\gui\auto_run_worker.py

src\claude_orchestrator\gui\claude_runner.py

src\claude_orchestrator\gui\main_window.py

src\claude_orchestrator\gui\ui_sections.py

src\claude_orchestrator\infrastructure\project_paths.py

9. 制約と注意点
9-1. GUI と Remote は直接通信しない

GUI と Remote Claude は直接メッセージ連携していない。
両者は同じ .claude_orchestrator を共有する 2 つのクライアントとして扱う。

9-2. 同一 task の同時操作は禁止

v1 では、同一 task を GUI と Remote Claude の両方から同時に操作しないこと。

例:

GUI で auto run 中の task に対して、Remote 側で run-task を実行しない

GUI 側で planner 実行中の task に対して、Remote 側で proposal 生成や task 作成をしない

9-3. Remote セッションの実体監視は限定的

remote_session.json は「起動要求を出した事実」と「最後に記録した状態」を保存している。
v1 では、Remote Claude セッションの生存確認を外部から厳密に追跡するところまでは実装していない。

そのため GUI 上の running は、厳密なセッション生存保証ではなく、起動記録ベースである。

9-4. GUI 側の自動再反映は限定的

Remote 側で .claude_orchestrator を更新した場合、GUI へ即座に自動反映されるとは限らない。
必要に応じて以下を行うこと。

一覧更新

再読込

task 再選択

状態再読込

10. v1 の価値

本実装の価値は、単に Remote ボタンを追加したことではない。
より重要なのは、GUI からしか使えなかった orchestrator 操作を、UseCase / CLI に寄せて共有基盤化できたことである。

これにより、今後以下の方向へ発展させやすくなった。

Remote Claude からの半自動オペレーション

通知機能の追加

GUI と Remote の役割分担

将来の Webhook / mobile 通知 / file watcher 追加

proposal からの直接実行フロー強化

11. 次工程候補

次工程候補は以下である。

11-1. GUI から「作成してそのまま実行」

現状は GUI で proposal から task を直接作成できるが、task 実行は別操作である。
次は以下の導線が考えられる。

task を直接作成して実行

11-2. 通知機能

task completed / blocked / stopped を通知する基盤を追加する。

候補:

GUI ログ + jsonl

Windows 通知

Webhook

ntfy / Slack / Discord など

11-3. Remote 状態の精度向上

remote_session.json の記録だけでなく、実際に remote セッションが稼働中かを確認できる仕組みを追加する。

11-4. GUI の自動再読込

Remote 側で task / planner / proposal が更新されたときに、GUI がより自然に追従できるようにする。

11-5. proposal_id の表示・仕様整理

CLI / docs / planner の proposal_id 表記を整理し、例示と実データのズレをなくす。

12. 最終結論

Remote Orchestrator v1 により、Claude Orchestrator GUI の既存処理を保ったまま、Remote Claude から同一 repo を共有して planner / proposal / task 実行を扱う基盤が整った。

本段階で成立している運用イメージは以下である。

ローカルでは GUI で状態を見る

Remote Claude は別セッションで起動する

Remote Claude は CLI で orchestrator を操作する

両者は .claude_orchestrator を共有して連携する

この構成を Remote Orchestrator v1 の基準構成とする。
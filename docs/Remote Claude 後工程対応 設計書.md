Remote Claude 後工程対応 設計書
1. 目的

本設計書は、claude_orchestrator の Remote Claude / Remote Operator を、
現在の GUI 実装に追従させるための後工程対応方針を定義するものである。

現状 GUI では、標準ライン実行後に以下の後工程が成立している。

planner 実行

plan_director 実行

adopt / no_adopt 判定

手動承認 / 自動承認

次 task 作成

次 task 自動実行

完了後停止予約

一方、Remote Claude 側は従来の proposal 中心フローに留まっており、
上記の後工程概念を十分に扱えていない。

本設計の目的は、Remote Claude 側にも GUI と同じ運用概念を導入し、
スマホ等からでも後工程を安全に操作できる状態へ近づけることである。

2. 現状と課題
2-1. 現状の Remote Claude フロー

現行 Remote Operator は主に以下の操作に対応している。

in_progress task の実行

completed task から proposal 作成

proposal 一覧表示

proposal 選択

proposal から task 作成

作成 task の実行

この構造は planner v1 相当のフローには合うが、
現行 GUI の後工程自動化には追従できていない。

2-2. 現状の不足点

現行 Remote Claude 側には以下が不足している。

planner 実行後の plan_director 実行

plan_director 結果表示

adopt / no_adopt に応じた分岐

次 task 承認待ち状態

手動承認 / 自動承認の切替

完了後停止予約

pipeline 全体の簡易状態表示

2-3. 影響

このままでは GUI と Remote Claude の機能差が広がり、

GUI ではできるが Remote ではできない

Remote では旧フロー、GUI では新フロー

という二重運用になりやすい。

その結果、

操作ミス

状態認識のズレ

実装保守の複雑化

が起きやすくなる。

3. 対応方針
3-1. 既存 Remote Operator を拡張する

Remote Claude 用の機構を全面作り直すのではなく、
既存の controller / renderer / remote_session_store を拡張する。

これにより、現在の数字入力型メニューを維持しつつ、
後工程概念を追加できる。

3-2. GUI と同じ概念を Remote に持ち込む

Remote 側でも最低限、以下の状態を扱えるようにする。

planner 実行

plan_director 実行

approval mode

stop reservation

waiting next task approval

last plan_director result

3-3. まずは「簡易 pipeline 制御」を目指す

初期対応では GUI と完全同一 UI を目指さない。
Remote 側ではテキストベースで十分なので、

何が起きているか分かる

何を選べばよいか分かる

危険な状態が見える

ことを優先する。

4. 対応範囲

今回の Remote Claude 後工程対応では、最低限以下を範囲とする。

追加対象

planner 実行

plan_director 実行

plan_director 結果表示

承認待ち処理

手動承認 / 自動承認切替

完了後停止予約

簡易 pipeline 状態表示

今回は後回しにするもの

GUI と同等の詳細レポート全文表示

planner proposal の高度な状態編集

pipeline role ごとの詳細色分け相当表現

複数 cycle をまたぐ高度比較表示

5. 機能要件
5-1. planner 実行

Remote から completed task を選択し、planner を実行できること。

最低要件

selected task が completed の場合のみ実行可能

実行後、proposal 一覧または post-planning メニューへ進む

5-2. plan_director 実行

planner 実行後に plan_director を実行できること。

最低要件

planner report が存在すること

実行結果として decision を取得できること

selected proposal / selection reason を表示できること

5-3. 手動承認

approval mode が manual の場合、plan_director が adopt を返したときに承認待ちへ遷移すること。

必要操作

次 task 作成を承認

今回は作成しない

5-4. 自動承認

approval mode が auto の場合、plan_director が adopt を返したときに承認待ちへ入らず次 task 作成へ進むこと。

制約

セッション中のみ有効

repo 切替で manual に戻る

Remote セッション再初期化時も manual に戻る

5-5. 完了後停止予約

Remote から「現在 task 完了後に停止」を予約できること。

最低要件

in_progress task 実行前または実行中の制御対象として扱えること

停止予約 ON/OFF を確認できること

5-6. pipeline 状態表示

Remote からも後工程の簡易状態が分かること。

表示したい内容

selected task

status

current_stage

next_role

approval_mode

stop reservation

last plan_director decision

waiting_next_task_approval の有無

6. 状態設計

Remote でも GUI 相当の一時状態が必要になるため、
RemoteSessionStore の保存項目を拡張する。

6-1. 追加項目
approval mode

approval_mode

manual

auto

stop reservation

stop_after_current_task_requested

true / false

next task approval

waiting_next_task_approval

true / false

last plan_director result

last_plan_director_decision

last_plan_director_selected_proposal_id

last_plan_director_selection_reason

planner context

last_planner_role

後工程元 task

post_run_source_task_id

6-2. 初期値

新規セッション開始時は以下とする。

approval_mode = manual

stop_after_current_task_requested = false

waiting_next_task_approval = false

last_plan_director_decision = ""

last_plan_director_selected_proposal_id = ""

last_plan_director_selection_reason = ""

last_planner_role = "planner_safe"

post_run_source_task_id = ""

6-3. リセット条件

以下のとき approval mode は manual に戻す。

repo 切替

mark_started()

reset_operator_state()

clear()

7. メニュー設計

現状の数字入力方式は維持しつつ、後工程メニューを追加する。

7-1. 現状メニュー

MENU_MAIN

MENU_IN_PROGRESS_TASK_LIST

MENU_COMPLETED_TASK_LIST

MENU_TASK_LIST

MENU_SELECTED_TASK

MENU_PROPOSAL_LIST

MENU_SELECTED_PROPOSAL

MENU_CREATED_TASK

MENU_POST_RUN

MENU_EXITED

7-2. 追加メニュー案
MENU_POST_PIPELINE

task 実行後または completed task 選択後に、後工程操作へ進むためのメニュー。

MENU_PLAN_DIRECTOR_RESULT

plan_director の結果を表示するメニュー。

MENU_NEXT_TASK_APPROVAL

manual mode 時の承認待ちメニュー。

MENU_PIPELINE_SETTINGS

approval mode / stop reservation を切り替える設定メニュー。

8. メニュー遷移案
8-1. task 実行後
in_progress task 実行

RunTaskUseCase 実行後:

status が completed なら
MENU_POST_PIPELINE

それ以外なら
既存 MENU_POST_RUN

8-2. completed task 選択後

completed task を選択したら、直接 proposal 一覧ではなく
MENU_POST_PIPELINE へ進める。

8-3. post pipeline メニューの候補

planner 実行

plan_director 実行

承認モード切替

停止予約切替

task 一覧へ戻る

メインメニューへ戻る

8-4. plan_director 実行後
no_adopt

MENU_PLAN_DIRECTOR_RESULT

結果表示

戻る

adopt かつ manual

MENU_NEXT_TASK_APPROVAL

adopt かつ auto

自動で task 作成

MENU_CREATED_TASK または MENU_POST_RUN 相当へ進む

9. 表示設計
9-1. main menu

メインメニューの上部に簡易状態を出せるとよい。

表示候補

approval_mode

stop reservation

selected task

current menu

ただし初版では last_message ベースでもよい。

9-2. post pipeline menu

ここは新たに以下を表示する。

source task id

status

approval mode

stop reservation

last planner role

last plan_director decision

9-3. plan_director result

最低限以下を表示する。

decision

selected_proposal_id

selection_reason

9-4. next task approval

manual mode 時は以下を表示する。

adopt 結果

selected proposal

次 task 作成を承認

今回は作成しない

戻る

10. controller 実装方針
10-1. 追加 usecase

RemoteOperatorController で新たに使うもの:

RunPlanDirectorUseCase

CreateTaskFromPlanDirectorUseCase

必要に応じて:

planner role 切替対応時は GenerateNextTaskProposalsUseCase の role 指定

10-2. 追加処理

controller に以下の責務を追加する。

planner 実行メソッド

plan_director 実行メソッド

manual / auto approval 分岐

stop reservation 切替

approval mode 切替

post pipeline 状態更新

10-3. 注意点

Remote 側でも GUI と同様に、

承認モード変更は running 中でも可

変更は次の未確定判定から有効

すでに承認待ちに入った案件へは遡及しない

を守る。

11. renderer 実装方針

RemoteOperatorRenderer はテキスト出力専用とし、
ロジックは持たせない。

追加する render 候補

render_post_pipeline_menu()

render_plan_director_result_menu()

render_next_task_approval_menu()

render_pipeline_settings_menu()

表示原則

1画面で情報を詰め込みすぎない

最低限の現在状態だけ先頭に出す

選択肢は番号で明確化する

12. RemoteSessionStore 実装方針

RemoteSessionStore に新規項目を追加する。

修正箇所

RemoteSessionInfo dataclass

to_dict()

load_info()

_build_default_payload()

_normalize_payload()

mark_started()

reset_operator_state()

注意点

approval mode は永続設定ではなく、
セッション文脈の一時設定として扱う。

13. 実装順
Phase 1

RemoteSessionStore 拡張

Phase 2

renderer.py に後工程用メニュー追加

Phase 3

controller.py に

planner

plan_director

承認待ち

自動承認
の分岐追加

Phase 4

approval mode / stop reservation の切替追加

Phase 5

Remote prompt 文面の見直し
必要なら remote_operator.txt テンプレートも更新

14. 変更対象ファイル
更新対象

src\claude_orchestrator\application\remote_operator\controller.py

src\claude_orchestrator\application\remote_operator\renderer.py

src\claude_orchestrator\application\usecases\remote_operator_usecase.py

src\claude_orchestrator\gui\services\remote_prompt_service.py

src\claude_orchestrator\infrastructure\remote_session_store.py

追加利用対象

RunPlanDirectorUseCase

CreateTaskFromPlanDirectorUseCase

15. 今回の完了条件

この後工程対応の完了条件は以下とする。

Remote から planner を実行できる

Remote から plan_director を実行できる

adopt / no_adopt 結果を確認できる

manual mode で承認待ちへ入れる

auto mode で自動作成へ進める

stop reservation を Remote から切り替えられる

approval mode がセッション限定で機能する

GUI と Remote の概念差が大きく減っている
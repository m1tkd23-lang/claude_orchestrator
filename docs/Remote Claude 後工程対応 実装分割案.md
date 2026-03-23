Remote Claude 後工程対応 実装分割案
1. 実装方針

今回は一気に完成形へ入れず、状態 → 表示 → 分岐 → 自動化 の順で段階的に入れます。

理由は次です。

RemoteSessionStore の状態が先に無いと分岐が安定しない

renderer を先に拡張すると controller の追加先が明確になる

自動承認や停止予約は最後に入れた方が事故が少ない

2. 実装フェーズ
Phase 1: 状態保持層の拡張

まず RemoteSessionStore を拡張します。

対象ファイル

src\claude_orchestrator\infrastructure\remote_session_store.py

追加するもの

approval_mode

stop_after_current_task_requested

waiting_next_task_approval

last_plan_director_decision

last_plan_director_selected_proposal_id

last_plan_director_selection_reason

last_planner_role

post_run_source_task_id

この段階のゴール

Remote 側でも GUI 相当の後工程状態を保持できる

approval mode は manual を既定値にできる

repo 切替 / セッション再初期化時の戻し先が定義できる

Phase 2: メニュー表示の拡張

次に renderer を拡張します。

対象ファイル

src\claude_orchestrator\application\remote_operator\renderer.py

追加するもの

render_post_pipeline_menu()

render_plan_director_result_menu()

render_next_task_approval_menu()

render_pipeline_settings_menu()

表示したい内容

approval mode

stop reservation

selected task

plan_director result

adopt / no_adopt の分岐案内

この段階のゴール

Remote の画面文面だけで後工程が理解できる

controller 側で使う新メニューの見た目が揃う

Phase 3: 定数とメニュー体系の拡張

controller に入る前に menu 定数を追加します。

対象ファイル

src\claude_orchestrator\application\remote_operator\constants.py

追加候補

MENU_POST_PIPELINE

MENU_PLAN_DIRECTOR_RESULT

MENU_NEXT_TASK_APPROVAL

MENU_PIPELINE_SETTINGS

この段階のゴール

controller 実装時に遷移名が先に固まっている

render / handle の対応が取りやすい

Phase 4: controller に後工程の骨格を追加

ここで controller を拡張します。

対象ファイル

src\claude_orchestrator\application\remote_operator\controller.py

追加するもの

planner 実行 分岐

plan_director 実行 分岐

post_pipeline メニュー分岐

plan_director_result メニュー分岐

next_task_approval メニュー分岐

pipeline_settings メニュー分岐

新たに使う usecase

RunPlanDirectorUseCase

CreateTaskFromPlanDirectorUseCase

この段階ではまだ簡易でよいもの

planner role はまず固定で planner_safe

停止予約は状態保存だけでもよい

自動承認はまだ最後に接続してもよい

この段階のゴール

Remote で planner → plan_director → 結果確認 の流れが通る

adopt / no_adopt をテキストで扱える

Phase 5: manual 承認フローの実装

次に、手動承認モードを成立させます。

対象ファイル

controller.py

renderer.py

remote_session_store.py

実装内容

approval_mode == manual のとき

adopt なら MENU_NEXT_TASK_APPROVAL

承認

今回は作成しない

この段階のゴール

GUI と同じく「承認待ち」が Remote でも成立する

Phase 6: auto 承認フローの実装

manual が安定したあとに auto を入れます。

対象ファイル

controller.py

remote_session_store.py

実装内容

approval_mode == auto

plan_director が adopt

承認待ちに入らず task 作成

必要なら created task メニューへ進む

守る仕様

セッション中のみ有効

repo 切替で manual

セッション再初期化でも manual

変更は次の未確定判定から有効

すでに承認待ちの案件へは遡及しない

この段階のゴール

GUI の自動承認概念と揃う

Phase 7: 停止予約の実装

最後に停止予約を追従させます。

対象ファイル

controller.py

renderer.py

remote_session_store.py

実装内容

停止予約 ON

停止予約 OFF

post pipeline メニューや settings メニューで確認

注意点

Remote 側だけで完結せず、実際の task 実行や後工程起動時の分岐にどう反映するかを明確にする必要があります。
ここは GUI の停止予約と意味を揃える前提で入れます。

この段階のゴール

Remote 側でも後工程停止ポリシーを扱える

3. ファイル単位の分割案
3-1. 最小変更で進める案

既存構造をなるべく維持するなら次です。

更新ファイル

src\claude_orchestrator\infrastructure\remote_session_store.py

src\claude_orchestrator\application\remote_operator\constants.py

src\claude_orchestrator\application\remote_operator\renderer.py

src\claude_orchestrator\application\remote_operator\controller.py

src\claude_orchestrator\application\usecases\remote_operator_usecase.py

src\claude_orchestrator\gui\services\remote_prompt_service.py

新規追加なし

まずはこれで十分です。

3-2. controller が太くなりそうな場合の分割案

もし途中で controller.py が膨らむなら、次を追加するのが自然です。

新規候補

src\claude_orchestrator\application\remote_operator\post_pipeline_helpers.py

src\claude_orchestrator\application\remote_operator\session_state_helpers.py

役割
post_pipeline_helpers.py

plan_director 実行

result 要約

approval 分岐

created task 分岐

session_state_helpers.py

session payload 更新補助

approval mode 更新

stop reservation 更新

plan_director result 書き込み

ただし初回は、まず既存ファイル内で収めて問題ありません。

4. 実装順のおすすめ

最も安全なのは次です。

Step 1

remote_session_store.py

Step 2

constants.py

Step 3

renderer.py

Step 4

controller.py に post pipeline 骨格追加

Step 5

controller.py に manual approval 追加

Step 6

controller.py に auto approval 追加

Step 7

controller.py / renderer.py に stop reservation 追加

Step 8

remote_prompt_service.py の文面更新

5. 実装ごとの確認ポイント
Phase 1 完了時

state json に新項目が入る

default 値が壊れていない

Phase 2 完了時

renderer 単体で後工程メニュー文字列が出せる

Phase 3-4 完了時

completed task から planner / plan_director へ進める

Phase 5 完了時

adopt 時に承認待ちへ入る

no_adopt では承認待ちに入らない

Phase 6 完了時

auto mode で承認待ちをスキップする

manual mode に戻すと従来通りになる

Phase 7 完了時

stop reservation ON/OFF が保持される

メニュー表示に反映される

6. 今回の実装スコープのおすすめ

一気に最後まで行くより、まずは Phase 1〜5 までで一区切りが良いです。

つまり最初の到達目標は次です。

Remote で planner 実行

Remote で plan_director 実行

Remote で decision 確認

manual approval で承認待ち

承認 / 見送りができる

そのあとに

auto approval

stop reservation

を足す方が安全です。

7. 次アクション

次に進むなら、
Phase 1〜3 の対象ファイル全文案 から作り始めるのが最もやりやすいです。
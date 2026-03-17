# docs\design_principles_gui_ready.md

# claude_orchestrator 設計原則書（GUI拡張前提版）

## 1. 文書の目的

本書は、claude_orchestrator を今後継続的に開発していくための設計原則を定義する。

claude_orchestrator は、Claude Code を役割ごとに分離して運用し、
対象リポジトリに対する実装・レビュー・指示のワークフローを管理する親アプリである。

現段階では CLI ベースで開発を進めるが、
将来的に GUI 化し、対象 repo 選択、タスク管理、進行状況表示、ログ表示、
コンソール状況表示などを扱えるように拡張することを前提とする。

本書の目的は以下である。

- 開発中に設計がぶれないようにする
- CLI 実装と将来 GUI 実装を両立できるようにする
- 親アプリと対象 repo の責務を明確にする
- Claude と Python の役割分担を固定する
- 機能追加時に守るべき原則を明文化する


## 2. アプリの基本コンセプト

claude_orchestrator は、Claude を直接自動制御するアプリではなく、
Claude Code を役割ごとの作業員として活用し、
Python がワークフロー管理を行う半自動オーケストレーションアプリである。

このアプリは以下の思想で設計する。

- Claude は知的処理担当
- Python は工程管理担当
- 対象 repo は実作業の現場
- orchestrator は対象 repo に運用基盤を配備し、外側から管理する

claude_orchestrator 自身が巨大な知能を持つ必要はない。
知的判断は Claude 側に委譲し、
Python 側は状態管理、フラグ判定、遷移制御、テンプレ生成に徹する。

この責務分離を崩さないことを最重要原則とする。


## 3. 開発方針

### 3-1. 今は CLI で開発する

初期実装は CLI ベースで行う。

理由:
- フロー設計の検証がしやすい
- GUI 実装コストを後回しにできる
- 状態遷移、JSON スキーマ、役割分担の妥当性確認を先に進められる

### 3-2. ただし最初から GUI 拡張可能な構造にする

CLI で始めるが、内部ロジックは GUI からも再利用できる形で設計する。

禁止事項:
- CLI コマンドの中に業務ロジックを直接書き込む
- 画面前提の処理を core に混ぜる
- 後で GUI から呼べない形で状態管理を実装する

### 3-3. GUI は後で追加する

将来的に GUI 化して以下を実現できるようにする。

- 対象 repo 選択
- 初期セットアップ実行
- タスク一覧表示
- 現在状態表示
- 次役の表示
- prompt 内容表示
- クリップボードコピー
- 作業ログ表示
- JSON 検証結果表示
- 開いているコンソール状態表示
- blocked タスクの可視化

GUI は後で追加するが、
今の設計はその追加を邪魔しないことを前提とする。


## 4. 対象とする運用モデル

### 4-1. 対象 repo

実際の開発対象 repo を対象 repo と呼ぶ。

例:
- drawing_review_app
- file_copipe_gui
- そのほか将来の任意 repo

### 4-2. 親アプリ

claude_orchestrator は対象 repo の外側に存在する親アプリである。

親アプリの役割:
- 対象 repo 選択
- 初期セットアップ
- task 作成
- state 管理
- prompt 生成
- report 検証
- 次フロー判定
- ログ管理

### 4-3. 対象 repo への配備

対象 repo には、claude_orchestrator が必要な運用ファイル一式を配備する。

想定する標準フォルダ:
- .claude_orchestrator/roles
- .claude_orchestrator/schemas
- .claude_orchestrator/templates
- .claude_orchestrator/config
- .claude_orchestrator/tasks
- .claude_orchestrator/runtime

対象 repo 側には、
Claude が参照する役割定義、JSON schema、テンプレート、task データを置く。


## 5. 役割分担の原則

### 5-1. Claude がやること

Claude は以下を担当する。

- 与えられた役割定義を読む
- 与えられた task / report / prompt を読む
- 実装、レビュー、指示の知的判断を行う
- 決められた JSON 形式で report を出力する

### 5-2. Python がやること

Python は以下を担当する。

- task 作成
- state 作成と更新
- report ファイル検知
- JSON schema 検証
- フラグ確認
- 次ロール判定
- prompt 組み立て
- 進行状況表示
- ログ保存

### 5-3. Python がやらないこと

Python は以下を行わない。

- 実装方針の知的判断
- レビュー内容の知的判断
- 承認の知的判断
- Claude report の内容生成

### 5-4. Claude がやらないこと

Claude は以下を行わない前提で運用する。

- workflow 状態遷移の最終管理
- state.json の勝手な変更
- 自分の役割外の権限行使
- schema 定義の変更
- 運用ルールの勝手な拡張


## 6. 初期役割構成

初期役割は 3 役とする。

### 6-1. implementer
責務:
- 実装
- 実施内容の報告
- 未解決点、確認不足、懸念の明示

### 6-2. reviewer
責務:
- implementer の結果レビュー
- 問題点、危険点、確認不足の指摘
- OK / needs_fix / blocked の判断

### 6-3. director
責務:
- implementer / reviewer の結果を見て次行動を決定
- approve / revise / stop の判断
- implementer へ戻す指示の整理

### 6-4. 将来拡張
役割は将来的に増やせる設計とする。

追加候補例:
- tester
- architect
- documenter
- security_reviewer

ただし、初期段階では 3 役で固定し、
まずワークフローを安定させることを優先する。


## 7. セッション運用原則

### 7-1. Claude Code は毎回新規セッションを使う

同じ Claude Code セッションを長時間使い回さない。

理由:
- 過去文脈が蓄積して処理が重くなる
- 役割純度が落ちる
- 以前の会話の影響を受けやすくなる
- 作業単位ごとの独立性が落ちる

### 7-2. Claude Code は常駐作業員ではなく単発作業員とみなす

1役 1回 1仕事を基本とする。

流れ:
- prompt を受ける
- 作業する
- JSON report を返す
- そのセッションは終了する

### 7-3. 親アプリは継続してよい

親Pythonは状態管理者であり、必要に応じて継続利用してよい。
ただし、常駐監視を必須にはしない。
初期段階では手動 advance 方式でもよい。


## 8. ワークフロー設計原則

### 8-1. 最初は半自動でよい

最初から完全自動化を目指さない。

初期段階では、
- Python が次 role 向け prompt を生成
- 人が Claude Code に貼り付け
- Claude が JSON report を出力
- Python がそれを検証し遷移

という半自動構成でよい。

### 8-2. UI 自動操作は後回し

以下は初期実装の対象外とする。

- コンソール自動起動
- `claude` 自動起動
- 画面フォーカス制御
- 入力欄への自動貼り付け
- Enter 自動送信

理由:
- 壊れやすい
- デバッグしにくい
- 本質は workflow と schema にある

### 8-3. クリップボード支援は将来導入してよい

初期実装後、必要に応じて以下を追加してよい。

- prompt を自動でクリップボードへコピー
- 保存先 JSON パスの表示
- 次 role の案内表示

これは GUI 化前の軽量な作業効率化として有効である。


## 9. 状態管理原則

### 9-1. state を中心に回す

親アプリは state.json を中心に workflow を管理する。

state が持つべき主情報:
- task_id
- cycle
- status
- current_stage
- next_role
- last_completed_role
- max_cycles

### 9-2. report フラグで遷移する

各 report は、親が見て次遷移を判断できる最小フラグを持つ。

例:
- implementer: done / blocked / need_input
- reviewer: ok / needs_fix / blocked
- director: approve / revise / stop

### 9-3. Python は report を信用しすぎない

Claude が出した JSON は必ず Python 側で検証する。

検証内容:
- JSON として正しいか
- schema に合致するか
- role が正しいか
- task_id が一致するか
- cycle が一致するか
- 必須キーが存在するか

Claude の出力は有用だが、門番なしで通さない。


## 10. JSON 運用原則

### 10-1. Claude は JSON のみ返す

各役割は report 出力時に JSON のみ返すことを原則とする。

禁止:
- コードフェンス付き JSON
- 前置き文
- 補足雑談
- Markdown 化された説明

### 10-2. schema は厳格に保つ

report 形式は固定し、後方互換なしの安易な変更を避ける。

schema 変更時は:
- version を上げる
- 影響範囲を明示する
- 既存 task との互換を確認する

### 10-3. 空値ルールを決める

不明項目は以下のように扱う。

- 単一値: 空文字または null
- 配列: 空配列
- 判断不能: blocked / need_input / stop などの明示フラグ

曖昧な自然文で埋めない。


## 11. 対象 repo への配備原則

### 11-1. 配備は親アプリが行う

対象 repo への `.claude_orchestrator/` 配備は親アプリの責務とする。

### 11-2. 配備内容は標準テンプレで管理する

親アプリは内蔵テンプレートを持ち、対象 repo に流し込む。

対象:
- roles
- schemas
- templates
- config
- tasks
- runtime

### 11-3. 対象 repo ごとの差分は project_config に閉じ込める

repo ごとの差はできる限り config に閉じ込める。

例:
- role 有効化一覧
- max_cycles
- task 命名規則
- strict mode
- 保存ポリシー

roles や core ロジックを repo ごとに分岐だらけにしない。


## 12. CLI / GUI 両立原則

### 12-1. CLI は薄くする

CLI 層は usecase 呼び出し専用とする。

### 12-2. GUI も同じ usecase を呼ぶ

将来 GUI は CLI と同じ application/usecase 層を呼ぶ。

### 12-3. core は UI 非依存とする

core は以下を知らないものとする。

- CLI 引数
- GUI 部品
- 画面表示
- クリップボード UI
- ウィンドウ状態

### 12-4. ログ取得は GUI から読みやすくする

ログは将来 GUI で一覧表示しやすい形を意識する。

例:
- task 単位ログ
- 時系列イベントログ
- エラーイベントログ
- 検証結果ログ


## 13. 推奨レイヤ構成

将来的な標準構成は以下を推奨する。

- core
  - 状態遷移
  - workflow 判定
  - schema 検証
  - prompt 組み立てロジック

- application
  - init_project
  - create_task
  - show_next
  - validate_report
  - advance_task
  - get_status

- infrastructure
  - file I/O
  - JSON 読み書き
  - ログ保存
  - クリップボード補助
  - プロセス補助

- cli
  - コマンド入口

- gui
  - 将来追加する画面入口

このレイヤ分離を壊さないこと。


## 14. 今後の実装優先順位

以下の順で実装を進める。

### 第1段階
- 設計原則の固定
- workflow ルール固定
- JSON schema 固定
- CLI コマンド仕様固定

### 第2段階
- 対象 repo 初期セットアップ機能
- task / state 管理
- prompt 生成
- report 検証
- advance

### 第3段階
- クリップボード支援
- ログ拡充
- status 表示強化

### 第4段階
- GUI 実装
- 対象 repo 選択 UI
- task 一覧 UI
- 状態表示 UI
- ログ表示 UI
- コンソール状態表示 UI

### 第5段階
- role 拡張
- 高度な運用支援
- 半自動化支援強化


## 15. 現段階の設計結論

claude_orchestrator は以下の方針で開発する。

- 今は CLI で作る
- ただし GUI 拡張前提で層分離する
- Claude は毎回新規セッションで使う
- Claude は JSON report を作る
- Python は JSON を検知・検証・遷移する
- まずは 3役で回す
- 役割増設可能な設計にする
- 対象 repo に `.claude_orchestrator/` を配備する
- 本質は UI 自動操作ではなく workflow 設計にある

この原則を、今後の実装判断の基準とする。
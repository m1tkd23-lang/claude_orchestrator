# src\claude_orchestrator\template_assets\project_bundle\.claude_orchestrator\docs\project_core\docs運用ルール.md
# docs運用ルール

## 目的

本ルールは、`.claude_orchestrator/docs/` 配下の文書を
AI 実行時に破綻なく運用するための配置・参照・更新方針を定義する。

本ルールにより、以下を防ぐ。

- core docs と reference docs の役割混在
- planner が missing docs 提案に過度に引っ張られること
- task_router / planner に不要な長文文脈が流れ込むこと
- docs の保存場所や責務の揺れ
- 運用中の文書追加による設計破綻

---

## 正本

docs の正本は以下とする。

`src/claude_orchestrator/template_assets/project_bundle/.claude_orchestrator/docs/`

各開発 repo では、初期化後に以下へ展開されたものを参照する。

`.claude_orchestrator/docs/`

人間向けの本体 repo 直下 `docs/` は補助資料置き場であり、
AI 実行時の正本ではない。

---

## 基本方針

- docs は役割別ディレクトリに整理する
- 1ファイル1目的を原則とする
- 常時読む文書は最小限にする
- task 固有の補助資料は reference docs として扱う
- 履歴文書は常時読ませない
- missing docs を planner の判断材料にしない
- 長文化した文書を core docs に昇格させない

---

## ディレクトリ責務

### `docs/project_core/`

プロジェクトの目的、判断軸、全体方針を置く。

特徴:
- role をまたいで有効
- 常時参照候補になりうる
- 比較的安定している
- 短く保つ

例:
- 開発の目的本筋.md
- docs運用ルール.md

---

### `docs/task_maps/`

TASK 処理や role 判断の地図を置く。

特徴:
- task_router / planner に特に有効
- フローや参照方針を整理する
- 実行判断補助として使う

例:
- TASKフロー全体図.md
- role別最小参照マップ.md
- planner_task_router判断材料マップ.md

---

### `docs/task_history/`

過去TASKの再利用知見を置く。

特徴:
- 常時参照しない
- 類似task時のみ補助的に使う
- ログ全文ではなく要約知見を残す

例:
- 過去TASK作業記録.md

---

## docs の分類

docs は以下の3分類で扱う。

### 1. core docs

常時 prompt に注入する固定文書。

条件:
- プロジェクト全体の軸になる
- task_router / planner の判断品質に直結する
- 短い
- 安定運用しやすい
- missing を許容しない

Phase 1 の core docs は以下の2本とする。

- `.claude_orchestrator/docs/project_core/開発の目的本筋.md`
- `.claude_orchestrator/docs/task_maps/planner_task_router判断材料マップ.md`

---

### 2. reference docs

task / planner 実行時に個別追加する補助文書。

条件:
- task 固有または機能固有
- 常時は不要
- planner の proposal 具体化に役立つ
- 存在確認済みのものだけ渡す

例:
- workflow_rules.md
- planner_v1_仕様書.md
- remote 関連仕様
- handover 文書
- 特定機能の設計メモ

重要:
- missing の reference docs は渡さない
- missing 情報を planner に見せない
- docs 不足を別管理課題として扱う場合は、人間側で task 化する

---

### 3. history docs

履歴・知見再利用用の文書。

条件:
- 類似task時のみ使う
- 常時は読ませない
- 長文化しすぎない
- 再発防止に役立つ

例:
- 過去TASK作業記録.md

---

## role ごとの docs 利用方針

### task_router

常時読む:
- 開発の目的本筋.md
- planner_task_router判断材料マップ.md

必要時のみ読む:
- TASKフロー全体図.md
- role別最小参照マップ.md
- 類似taskに関する過去TASK作業記録.md

---

### planner

常時読む:
- 開発の目的本筋.md
- planner_task_router判断材料マップ.md

必要時のみ読む:
- workflow_rules.md
- planner_v1_仕様書.md
- remote / GUI / planner / workflow 関連の仕様書
- 類似taskに関する過去TASK作業記録.md

重要:
- reference docs は存在する文書だけ渡す
- missing docs は planner の入力に含めない

---

### implementer / reviewer / director

現時点では core docs を常時注入しない。

理由:
- prompt 肥大化を避けるため
- 実行品質は task_router / planner の上流整理で先に改善するため
- Phase 2 以降で必要性を再評価するため

---

## missing の扱い

### core docs

- 必須
- missing はエラー
- 実行を継続しない
- `FileNotFoundError` とする

---

### reference docs

- 任意
- missing は入力から除外する
- missing 情報を planner にそのまま渡さない
- 空配列 `[]` でもよい

---

### history docs

- 任意
- 利用しない場合は渡さない
- missing でも通常エラーにしない

---

## 命名と記述ルール

- ファイル名は内容を短く表す
- 見出しとファイル名をできるだけ揃える
- 1ファイル1目的
- core docs は特に短く保つ
- role 固有の詳細手順は docs より skill を優先する
- 実装ログ全文を docs に置かない
- 長い議論メモは本体 repo 直下 `docs/` 側で管理する

---

## 更新ルール

### core docs を更新する時

以下を確認する。

- 常時読み込みに耐える長さか
- task_router / planner の判断品質向上に直結するか
- 既存 core docs と役割重複していないか

---

### reference docs を追加する時

以下を確認する。

- 常時 docs にすべき内容ではないか
- task 固有・機能固有の補助資料として妥当か
- planner に渡す価値があるか
- 実在ファイルとして repo 内に存在するか

---

### history docs を更新する時

以下を守る。

- 長文ログ全文にしない
- 再利用知見だけ残す
- 類似task時に読んで意味がある内容だけ書く

---

## 運用メモ

- docs は増やす前に分類を決める
- まず core / reference / history のどれかを決める
- 判断が迷う文書は reference docs から始める
- core docs は厳選する
- planner が docs 整備提案ばかり出す場合は、reference docs の渡し方を先に見直す
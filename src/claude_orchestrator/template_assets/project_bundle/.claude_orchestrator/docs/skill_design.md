# skill_design

## 目的

本書は、`.claude_orchestrator/skills/` 配下で運用する skill の設計方針を定義する。

skill は、AI に毎回すべての細かい判断をさせるのではなく、  
**特定の役割・状況で必要な判断観点だけを最小限で追加するための補助文書**である。

本書の目的は以下のとおり。

- skill の役割を明確にする
- skill の増やしすぎを防ぐ
- task_router の skill 選定基準を安定させる
- implementer / reviewer の判断品質を揃える
- 新しい skill を追加するときのルールを固定する

---

## 基本方針

### 1. skill は最小限にする

skill は多ければよいものではない。  
必要な場面で必要なものだけ付与する。

避けるべき状態:

- とりあえず複数付ける
- 似た役割の skill を乱立させる
- task の規模に対して過剰な skill を付ける
- skill がないと動けない前提にする

---

### 2. skill は role 固有の補助である

skill は role を置き換えるものではない。  
role の主責務は role 定義にあり、skill はその role の判断や作業を補助する。

例:

- implementer は実装者であり、skill は実装手順の補助
- reviewer は評価者であり、skill は評価観点の補助
- task_router は routing 判断者であり、skill は routing 判断基準の補助

---

### 3. skill は prompt 肥大化を防ぐために存在する

すべての詳細手順を role 定義や template に直接書くと、prompt が重くなりやすい。  
そのため、必要な判断観点だけを skill として分離する。

ただし、分離しすぎると今度は構造が散らばるため、  
**汎用性があり、繰り返し使う判断観点だけを skill 化する**。

---

### 4. skill は実在ファイルのみを参照対象にする

`role_skill_plan` に含める skill は、repo 内に実在するものだけにする。

存在しない skill を plan に含めると実行時エラーになるため、  
「将来的に必要そう」なだけでは付与しない。

新しい skill が必要と判断した場合は:

- その場では `role_skill_plan` に含めない
- `skill_selection_reason` または `initial_execution_notes` に  
  **新規 skill 候補**として提案する

---

## skill の分類

現行の skill は、役割ごとに以下のように分類する。

### task_router
- `route-task`

### implementer
- `write-plan`
- `execute-plan`
- `debug-fix`
- `migration-safety-check`

### reviewer
- `code-review`
- `doc-consistency-review`

### director
- 現時点では未使用

---

## role ごとの skill 設計方針

### task_router

task_router の skill は、  
**task を安全に実行可能な形へ整理する判断基準** を与える。

task_router 用 skill は以下を満たすべき。

- task_type 判定に役立つ
- risk_level 判定に役立つ
- role_skill_plan の最小構成選定に役立つ
- implementer 開始前の注意点整理に役立つ

現時点では固定 skill `route-task` のみを使う。

---

### implementer

implementer の skill は、  
**実装や検証の進め方を過不足なく絞るための補助** とする。

設計意図は以下のとおり。

- `write-plan`  
  変更前の整理を補助する
- `execute-plan`  
  実行フェーズを補助する
- `debug-fix`  
  bugfix 系の原因切り分けを補助する
- `migration-safety-check`  
  既存データ互換性確認を補助する

implementer 用 skill は、  
「何を作るか」よりも「どう安全に進めるか」を支えるものを優先する。

---

### reviewer

reviewer の skill は、  
**変更内容に応じた評価観点の切り替え** を担う。

- `code-review`  
  実装の安全性・範囲逸脱・整合性を確認する
- `doc-consistency-review`  
  文書の記述品質・論理整合・既存ルールとの一致を確認する

reviewer 用 skill は、  
コード中心 task と文書中心 task の評価軸を切り替えるために使う。

---

### director

director は現時点で専用 skill を持たない。  
理由は以下のとおり。

- director の判断は現状そこまで定型化されていない
- まずは task_router / implementer / reviewer の安定化を優先する
- director にまで細かな skill を増やすと、全体が複雑化しやすい

将来的に追加する場合は、  
収束判断や revise 条件の定型観点が十分に蓄積されてから検討する。

---

## skill 追加の判断基準

新しい skill を追加してよいのは、以下を満たす場合に限る。

### 追加してよい条件

- 複数 task で繰り返し有効
- 既存 skill では代替しにくい
- role 定義や template に直接書くより分離したほうがよい
- 判断や作業品質のばらつきを減らせる
- 名前から用途が明確に分かる

### 追加しないほうがよい条件

- 単発 task 専用
- 既存 skill の言い換えにすぎない
- task title / description / constraints だけで十分判断できる
- role 定義に1〜2行足せば済む
- 付与条件が曖昧で task_router が迷いやすくなる

---

## skill 名のルール

skill 名は以下の方針で付ける。

- 短い
- 動作や目的が分かる
- role に依存しすぎない一般名にする
- ハイフン区切りを使う
- 何をする skill か推測しやすい名前にする

例:
- `write-plan`
- `execute-plan`
- `debug-fix`
- `code-review`

避ける例:
- `do-task-well`
- `smart-check`
- `misc-helper`

---

## task_router による skill 付与の原則

task_router は skill を付与するとき、以下の優先順で考える。

1. task の主目的
2. 変更対象の種類
3. 影響範囲
4. 既存構造を壊す危険性
5. reviewer の評価観点の切り替え要否

task_router は、  
「使える skill を全部付ける」のではなく、  
**この task を安全に進めるために必要な最小構成** を選ぶ。

---

## docs と skill の責務分離

### docs に書くもの
- 全体方針
- プロジェクトの目的
- フロー地図
- role別の参照方針
- skill の設計思想

### skill に書くもの
- 具体的な判断手順
- 実行手順
- レビュー観点
- 付与条件の操作レベルの説明

つまり、

- `docs/skill_design.md` は **設計思想**
- `skills/.../*.md` は **実務手順**

として分ける。

---

## 運用ルール

### skill を追加したら必ず行うこと

1. 実ファイルを `skills/<role>/` に追加する
2. `route-task.md` の利用可能 skill 一覧を更新する
3. 必要なら付与条件を更新する
4. 本書 `skill_design.md` の設計方針と矛盾しないか確認する
5. task を数件回して過不足を確認する

---

### skill を廃止・統合する時の方針

- いきなり削除しない
- まず task_router で付与しない運用にする
- 既存 task との整合を確認する
- 代替 skill が明確な場合のみ統合する

---

## 現時点での設計判断

現段階では、  
**task_router と planner の判断品質を先に高めること** を優先する。

したがって、skill の追加もまずは以下を優先する。

- task_router の routing 精度向上
- implementer の実装暴走防止
- reviewer の評価観点安定化

director 専用 skill や細分化しすぎた skill は、  
必要性が明確になるまで追加しない。

---

## 運用メモ

- skill は少ないほどよい
- ただし少なすぎて判断がぶれるなら増やしてよい
- 迷ったらまず docs や role 定義で吸収できないかを先に考える
- それでも繰り返し困るなら skill 化を検討する
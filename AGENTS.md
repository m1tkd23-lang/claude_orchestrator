# AGENTS.md

## プロジェクト概要

このリポジトリは **claude_orchestrator** であり、
タスク駆動型の AI 開発ワークフローを管理するためのシステムです。

基本思想:

* task / state / report を唯一の実行根拠とする
* 各 role（task_router / implementer / reviewer / director）で工程を分離する
* validate / advance により工程ゲートを強制する
* AIの能力ではなく「プロセス設計」で再現性を担保する

---

## 最重要ルール（必ず守る）

### 1. 推測で実装しない

* 不明点がある場合は勝手に進めず、確認または安全な範囲で限定実装する

### 2. 既存のワークフローを壊さない

* validate / advance の挙動を変更してはいけない
* role の責務を越えた変更は禁止
* state 遷移ロジックを変更しない

### 3. JSON契約を絶対に壊さない

* report schema は変更しない
* task.json / state.json の構造を変えない
* AI が出力する JSON 形式は維持する

### 4. fullデータは保存、compactは派生

* full report / full task / full docs は保存用
* prompt に渡す直前でのみ compact 化する
* 元データは絶対に破壊しない

---

## 開発方針

### 基本戦略

このプロジェクトは以下の順で最適化する:

1. Python 側で compact context を生成する
2. AI に渡す情報量を削減する
3. 必要に応じて AI 出力を見直す

---

### 現在の最適化方針（重要）

現在は以下を進めている:

* execution系 report の compact 化（完了済み）
* planner / plan_director の compact 化
* docs（feature_inventory / task_history）の compact 化
* 長期記憶の導入準備

---

## 変更禁止領域

以下は基本的に変更禁止:

* schema ファイル（*.schema.json）
* validate_report_usecase
* advance_task_usecase
* workflow の state 遷移ロジック
* task.json / state.json の構造

変更が必要な場合は明確な理由と影響範囲を示すこと

---

## 修正対象として良い領域

主に以下を対象とする:

* services（compact / formatter）
* usecases（prompt生成部分）
* runtime（context組み立て）
* docs compact 処理

---

## 実装ルール

### 1. 変更は最小差分

* 必要な箇所だけ変更する
* unrelated なリファクタは禁止

### 2. 既存命名を維持

* template の変数名は可能な限り変更しない
* 互換性を優先する

### 3. deterministic に処理する

* AI に頼らず Python で処理する
* 要約ではなく「抽出」を優先

### 4. 空配列・空値は維持

* 再現性のため key を消さない

---

## compact 設計ルール

### report

* implementer → reviewer
* reviewer → director
* director → 次 role

すべて compact context に変換して渡す

### docs

#### feature_inventory.md

* 全文投入しない
* feature一覧を抽出して compact 化

#### 過去TASK作業記録.md

* 全文投入しない
* recent block 抽出
* 将来的に長期記憶へ移行

---

## 長期記憶（今後）

設計方針:

* SQLite で管理
* failure / revise / blocked を中心に記録
* prompt に 1〜3件だけ注入

注意:

* 現時点では未実装
* compact layer 完成後に導入

---

## 作業手順

1. 対象ファイルを読む
2. 影響範囲を特定
3. 最小差分で修正
4. prompt 出力を確認
5. 情報欠落がないか確認

---

## 出力ルール

コードを出力する場合:

* 必ず全文出力
* 1ファイル1コードブロック
* ファイル先頭に相対パスコメントを付ける

例:

```python
# src/claude_orchestrator/services/example.py
```

---

## テスト・確認

最低限確認すること:

* import エラーが出ない
* show_next_usecase が動く
* prompt が生成される
* compact が適用されている
* JSON構造が崩れていない

---

## NG例

以下は禁止:

* 「全体を最適化した」
* 「いい感じに整理した」
* 「全部書き直した」

---

## OK例

* 「この3ファイルのみ修正」
* 「この関数のみ変更」
* 「このキーのみ削減」

---

## 最後に

このプロジェクトの目的は:

> AIを賢くすることではなく、プロセスを賢くすること

そのため、変更は常に:

* 再現性
* 安定性
* 最小情報

を優先すること

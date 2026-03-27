# carry_over 運用ガイド

**バージョン**: v0
**用途**: carry_over の標準運用ルール定義

---

## 概要

carry_over は、前 task の未解決リスクを次 task に引き継ぐ仕組みである。

本仕組みにより、

* 未解決リスクの取りこぼし防止
* task 間の文脈の連続性維持
* reviewer / director 指摘の継続反映

を実現する。

carry_over-v0 は **人手運用を前提とした基本フロー** であり、
Python 実装・schema の変更を伴わずに運用可能である。

---

## carry_over の対象

| 優先度   | 引き継ぎ元フィールド                           | 引き継ぎ条件                              |
| ----- | ------------------------------------ | ----------------------------------- |
| 高（必須） | `director_report.remaining_risks`    | 空でない場合は必ず carry_over する             |
| 中（任意） | `reviewer_report.nice_to_have`（未対処分） | 次 task が関連ドメインを扱う場合のみ任意で carry_over |

---

## 基本フロー

### 1. 前 task の director_report を確認する

前 task が完了した後、次 task 作成前に以下を確認する。

```
.claude_orchestrator/tasks/TASK-XXXX/inbox/director_report_v{N}.json
```

---

### 2. context_files に追加する

carry_over を行う場合、次 task の `context_files` に以下を追加する。

```json
"context_files": [
  ".claude_orchestrator/tasks/TASK-XXXX/inbox/director_report_v{N}.json"
]
```

---

### 3. initial_execution_notes の先頭に転記する

次 task の `task.json` において、
`initial_execution_notes` の **先頭** に以下形式で転記する。

```json
"initial_execution_notes": [
  "[carry_over from TASK-XXXX] {remaining_risks の内容}",
  "（以下、通常の初期実行注意事項）"
]
```

---

## フォーマット規則

* プレフィックス `[carry_over from TASK-XXXX]` を必ず付ける
* `remaining_risks` の文言は **改変しない**
* carry_over 項目は必ず先頭に配置する
* 配列順序は元の `remaining_risks` と一致させる

---

## task_router による転記

`task_router_prompt.txt` に carry_over 処理ルールが定義されている場合、

* `context_files` に `director_report_vN.json` が含まれていれば
* task_router はその指示に従い
* `remaining_risks` を `initial_execution_notes` の先頭に転記する

※これはプログラム処理ではなく、LLM のプロンプト指示に基づく動作である

---

## プレフィックス識別パターン

将来の自動処理・フィルタ処理のため、以下の形式を前提とする。

```
^\[carry_over from TASK-\d+\]
```

---

## v0 の制約

| 項目               | v0 の扱い |
| ---------------- | ------ |
| carry_over の累積上限 | 未定義    |
| 重複排除             | 未対応    |
| 優先度制御            | 未対応    |
| 自動選別             | 未対応    |

---

## 未定義事項

以下は v0 では扱わない。

* carry_over の最大件数制御
* 古い項目の削除ルール
* nice_to_have の明確な採用基準
* 複数 task からの統合戦略

---

## v1 / v2 拡張方針

### v1（自動化）

* context_files への自動追加
* task_router による自動転記の安定化

### v2（制御）

* 上限設定
* 重複排除
* 優先度付け
* 表示最適化

---

## 関連ファイル

| ファイル                                                    | 用途               |
| ------------------------------------------------------- | ---------------- |
| `.claude_orchestrator/templates/task_router_prompt.txt` | carry_over 転記ルール |
| `.claude_orchestrator/docs/project_core/開発の目的本筋.md`     | carry_over の基本定義 |

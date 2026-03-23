# carry_over-v1 実装仕様

## 概要

carry_over-v1 は、前 task の director_report.remaining_risks を  
次 task 作成時に自動的に引き継ぐ仕組みである。

v0 では人手および task_router に依存していたが、  
v1 では CreateTaskFromProposalUseCase にて自動処理を行う。

---

## v1 の目的

- carry_over の完全自動化
- 人手依存の排除
- task_router 依存の軽減
- 重要なリスクの取りこぼし防止

---

## 処理フロー

1. source_task_id から director_report を取得
2. remaining_risks を取得
3. carry_over 対象をフィルタ
4. context_files に director_report を追加
5. task_router により initial_execution_notes に転記

---

## carry_over 対象ルール（v1）

### 採用条件
- 空でない文字列

### 除外条件
- 以下のプレフィックスで始まるもの


[carry_over from TASK-XXXX]


（過去carry_overの再転記防止）

---

## 重複排除

- 完全一致の文字列は1件にまとめる

---

## v1 の制約

- schema変更なし
- Python変更は task生成処理のみ
- director / reviewer prompt 変更なし
- 優先度判定なし
- 件数制限なし

---

## v1 の設計判断

### 全件転記について
- 新規 remaining_risks は全件 carry_over する
- ただし過去 carry_over の再転記は禁止

---

## 未対応（v2以降）

- 優先度フィルタ
- 件数上限
- LLMによる要約
- nice_to_have の自動採用
- 関連ドメイン判定

---

## 対象ファイル

- create_task_from_proposal_usecase.py

---

## リスク

- remaining_risks の品質に依存
- director の記述品質が低い場合ノイズ混入

---

## 今後

v2 で以下を検討：

- priority構造化
- carry_over専用フィールド
- フィルタ強化